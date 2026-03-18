"""
Arducam ROS 2 Node
Wraps ArducamDepthCamera driver and publishes sensor data to ROS topics
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image, CameraInfo, PointCloud2
from sensor_msgs_py import point_cloud2
from geometry_msgs.msg import Point
from std_msgs.msg import Header
import numpy as np
import cv2
from cv_bridge import CvBridge

from .arducam_driver import ArducamDepthCamera


class ArducamNode(Node):
    """ROS 2 Node for Arducam depth camera sensor."""

    def __init__(self):
        super().__init__("arducam_node")

        # Declare parameters
        self.declare_parameter("camera_index", 0)
        self.declare_parameter("frame_width", 640)
        self.declare_parameter("frame_height", 480)
        self.declare_parameter("publish_rate", 30)
        self.declare_parameter("frame_id", "camera_depth")

        # Get parameters
        camera_index = self.get_parameter("camera_index").value
        frame_width = self.get_parameter("frame_width").value
        frame_height = self.get_parameter("frame_height").value
        publish_rate = self.get_parameter("publish_rate").value
        self.frame_id = self.get_parameter("frame_id").value

        # Initialize sensor
        self.camera = ArducamDepthCamera(
            camera_index=camera_index, width=frame_width, height=frame_height
        )

        if not self.camera.open():
            self.get_logger().error("Failed to open camera device")
            raise RuntimeError("Camera initialization failed")

        self.get_logger().info(
            f"Arducam camera opened: {frame_width}x{frame_height} @ {publish_rate}Hz"
        )

        # QoS profile
        qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )

        # Publishers
        self.rgb_publisher = self.create_publisher(Image, "camera/rgb/image", qos)
        self.depth_publisher = self.create_publisher(Image, "camera/depth/image", qos)
        self.pointcloud_publisher = self.create_publisher(
            PointCloud2, "camera/depth/points", qos
        )
        self.camera_info_publisher = self.create_publisher(
            CameraInfo, "camera/camera_info", qos
        )

        # CV Bridge
        self.bridge = CvBridge()

        # Timer for publishing
        period = 1.0 / publish_rate
        self.timer = self.create_timer(period, self.timer_callback)

        self.get_logger().info("ArducamNode started")

    def timer_callback(self):
        """Timer callback to read and publish sensor data."""
        try:
            # Read frame
            result = self.camera.read_frame()
            if result is None:
                return

            rgb_frame, depth_frame = result

            # Get current timestamp
            now = self.get_clock().now().to_msg()
            header = Header()
            header.stamp = now
            header.frame_id = self.frame_id

            # Filter depth
            depth_filtered = self.camera.filter_depth(depth_frame)

            # Publish RGB image
            rgb_msg = self.bridge.cv2_to_imgmsg(rgb_frame, encoding="bgr8")
            rgb_msg.header = header
            self.rgb_publisher.publish(rgb_msg)

            # Publish depth image (scaled for visualization)
            depth_display = (depth_filtered / 1000.0 * 255).astype(np.uint8)
            depth_msg = self.bridge.cv2_to_imgmsg(depth_display, encoding="mono8")
            depth_msg.header = header
            self.depth_publisher.publish(depth_msg)

            # Convert to 3D points and publish point cloud
            points_3d = self.camera.get_3d_points(depth_filtered)
            points_list = []

            h, w = depth_filtered.shape
            for v in range(h):
                for u in range(w):
                    x, y, z = points_3d[v, u]
                    # Filter out points with z = 0 (invalid depth)
                    if z > self.camera.depth_min_mm:
                        points_list.append([x, y, z])

            if points_list:
                points_array = np.array(points_list, dtype=np.float32)
                pc2_msg = point_cloud2.create_cloud_xyz32(
                    header, points_array
                )
                self.pointcloud_publisher.publish(pc2_msg)

            # Publish camera info
            camera_info = self.get_camera_info(header)
            self.camera_info_publisher.publish(camera_info)

        except Exception as e:
            self.get_logger().error(f"Error in timer callback: {e}")

    def get_camera_info(self, header: Header) -> CameraInfo:
        """Create and return camera info message."""
        camera_info = CameraInfo()
        camera_info.header = header
        camera_info.height = self.camera.height
        camera_info.width = self.camera.width

        # Intrinsic matrix (3x3)
        camera_info.k = [
            self.camera.fx,
            0.0,
            self.camera.cx,
            0.0,
            self.camera.fy,
            self.camera.cy,
            0.0,
            0.0,
            1.0,
        ]

        # Projection matrix (3x4)
        camera_info.p = [
            self.camera.fx,
            0.0,
            self.camera.cx,
            0.0,
            0.0,
            self.camera.fy,
            self.camera.cy,
            0.0,
            0.0,
            0.0,
            1.0,
            0.0,
        ]

        # Identity rotation matrix
        camera_info.r = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]

        camera_info.distortion_model = "plumb_bob"
        camera_info.d = [0.0, 0.0, 0.0, 0.0, 0.0]

        return camera_info

    def destroy_node(self):
        """Cleanup on node destruction."""
        if self.camera:
            self.camera.close()
        super().destroy_node()


def main(args=None):
    """Main entry point."""
    rclpy.init(args=args)
    node = ArducamNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
