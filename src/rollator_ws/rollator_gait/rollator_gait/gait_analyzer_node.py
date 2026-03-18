"""
Gait Analyzer ROS 2 Node
Subscribes to depth sensor data and publishes gait analysis results
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import PointCloud2, Image
from sensor_msgs_py import point_cloud2
from geometry_msgs.msg import Pose, Point
from std_msgs.msg import Float32MultiArray, Float32, String
import numpy as np
from dataclasses import asdict

from .gait_analyzer import GaitAnalyzer, GaitPhase


class GaitAnalyzerNode(Node):
    """ROS 2 Node for gait analysis."""

    def __init__(self):
        super().__init__("gait_analyzer_node")

        # Declare parameters
        self.declare_parameter("history_size", 30)
        self.declare_parameter("sampling_rate", 30)
        self.declare_parameter("legs_roi_top", 0.3)  # Top of legs region

        history_size = self.get_parameter("history_size").value
        sampling_rate = self.get_parameter("sampling_rate").value
        self.legs_roi_top = self.get_parameter("legs_roi_top").value

        # Initialize gait analyzer
        self.gait_analyzer = GaitAnalyzer(
            history_size=history_size, sampling_rate_hz=sampling_rate
        )

        # QoS profile
        qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=5,
        )

        # Subscribers
        self.pointcloud_subscription = self.create_subscription(
            PointCloud2, "camera/depth/points", self.pointcloud_callback, qos
        )

        # Publishers
        self.gait_metrics_publisher = self.create_publisher(
            Float32MultiArray, "gait/metrics", 10
        )
        self.stride_length_publisher = self.create_publisher(
            Float32, "gait/stride_length", 10
        )
        self.cadence_publisher = self.create_publisher(Float32, "gait/cadence", 10)
        self.symmetry_publisher = self.create_publisher(Float32, "gait/symmetry", 10)
        self.stability_publisher = self.create_publisher(
            Float32, "gait/stability", 10
        )
        self.gait_phase_publisher = self.create_publisher(
            String, "gait/phase", 10
        )
        self.leg_keypoints_publisher = self.create_publisher(
            Float32MultiArray, "gait/keypoints", 10
        )

        self.get_logger().info("GaitAnalyzerNode started")

    def pointcloud_callback(self, msg: PointCloud2):
        """Callback for point cloud data from depth sensor."""
        try:
            # Extract points from point cloud
            points = point_cloud2.read_points_numpy(msg)

            if len(points) == 0:
                return

            # Extract X, Y, Z coordinates (in mm)
            # Assuming point_cloud2 structure (x, y, z, ...)
            xyz = points[["x", "y", "z"]]

            # Simple leg detection heuristic
            # Detect lower body points based on Y position (height)
            # Adjust these thresholds for your camera setup
            lower_body_mask = xyz["y"] > 500  # Points below certain height

            if not np.any(lower_body_mask):
                return

            lower_body_points = xyz[lower_body_mask]

            # Cluster points to detect left and right legs
            left_leg_points, right_leg_points = self._cluster_legs(lower_body_points)

            if left_leg_points is None or right_leg_points is None:
                return

            # Extract keypoints from clusters
            left_keypoints = self._extract_keypoints(left_leg_points)
            right_keypoints = self._extract_keypoints(right_leg_points)

            if left_keypoints is None or right_keypoints is None:
                return

            # Process frame
            timestamp_us = int(msg.header.stamp.sec * 1e6 + msg.header.stamp.nanosec / 1000)

            frame = self.gait_analyzer.process_frame(
                timestamp_us=timestamp_us,
                left_hip=left_keypoints["hip"],
                left_knee=left_keypoints["knee"],
                left_ankle=left_keypoints["ankle"],
                left_foot=left_keypoints["foot"],
                right_hip=right_keypoints["hip"],
                right_knee=right_keypoints["knee"],
                right_ankle=right_keypoints["ankle"],
                right_foot=right_keypoints["foot"],
            )

            # Publish results
            self._publish_metrics(frame)

        except Exception as e:
            self.get_logger().error(f"Error in pointcloud callback: {e}")

    def _cluster_legs(self, points: np.ndarray):
        """
        Cluster lower body points into left and right legs.
        Simple approach: split by X coordinate.
        """
        if len(points) < 10:
            return None, None

        x_coords = points["x"]
        x_median = np.median(x_coords)

        left_mask = x_coords < x_median
        right_mask = x_coords > x_median

        left_leg_points = points[left_mask]
        right_leg_points = points[right_mask]

        if len(left_leg_points) < 5 or len(right_leg_points) < 5:
            return None, None

        return left_leg_points, right_leg_points

    def _extract_keypoints(self, leg_points: np.ndarray):
        """
        Extract leg keypoints (hip, knee, ankle, foot) from point cluster.
        Uses spatial distribution to identify joints.
        """
        try:
            x = leg_points["x"]
            y = leg_points["y"]
            z = leg_points["z"]

            # Sort by Y coordinate (height)
            sorted_indices = np.argsort(y)

            # Divide into segments (hip, thigh, shank, foot)
            n = len(sorted_indices)
            seg_size = n // 4

            # Hip: topmost points (lowest Y value)
            hip_idx = sorted_indices[:seg_size].mean()
            hip = np.array(
                [
                    x[int(hip_idx)],
                    y[int(hip_idx)],
                    z[int(hip_idx)],
                ]
            )

            # Knee: upper-middle segment
            knee_idx = sorted_indices[seg_size : 2 * seg_size].mean()
            knee = np.array(
                [
                    x[int(knee_idx)],
                    y[int(knee_idx)],
                    z[int(knee_idx)],
                ]
            )

            # Ankle: lower-middle segment
            ankle_idx = sorted_indices[2 * seg_size : 3 * seg_size].mean()
            ankle = np.array(
                [
                    x[int(ankle_idx)],
                    y[int(ankle_idx)],
                    z[int(ankle_idx)],
                ]
            )

            # Foot: lowest points (highest Y value)
            foot_idx = sorted_indices[3 * seg_size :].mean()
            foot = np.array(
                [
                    x[int(foot_idx)],
                    y[int(foot_idx)],
                    z[int(foot_idx)],
                ]
            )

            return {
                "hip": hip,
                "knee": knee,
                "ankle": ankle,
                "foot": foot,
            }

        except Exception as e:
            self.get_logger().debug(f"Error extracting keypoints: {e}")
            return None

    def _publish_metrics(self, frame):
        """Publish gait metrics."""
        metrics = frame.metrics

        # Publish individual metrics
        stride_msg = Float32()
        stride_msg.data = metrics.stride_length_mm
        self.stride_length_publisher.publish(stride_msg)

        cadence_msg = Float32()
        cadence_msg.data = metrics.cadence_steps_per_min
        self.cadence_publisher.publish(cadence_msg)

        symmetry_msg = Float32()
        symmetry_msg.data = metrics.symmetry_index
        self.symmetry_publisher.publish(symmetry_msg)

        stability_msg = Float32()
        stability_msg.data = metrics.stability_index
        self.stability_publisher.publish(stability_msg)

        # Publish gait phase
        phase_msg = String()
        phase_msg.data = f"L:{metrics.phase_left.name} R:{metrics.phase_right.name}"
        self.gait_phase_publisher.publish(phase_msg)

        # Publish all metrics as array
        metrics_array = Float32MultiArray()
        metrics_array.data = [
            metrics.stride_length_mm,
            metrics.cadence_steps_per_min,
            metrics.step_width_mm,
            metrics.knee_flexion_deg,
            metrics.hip_flexion_deg,
            metrics.gait_velocity_mm_s,
            metrics.symmetry_index,
            metrics.stability_index,
        ]
        self.gait_metrics_publisher.publish(metrics_array)

        # Publish keypoints
        keypoints_msg = Float32MultiArray()
        keypoints = [
            *frame.left_leg.hip,
            *frame.left_leg.knee,
            *frame.left_leg.ankle,
            *frame.left_leg.foot,
            *frame.right_leg.hip,
            *frame.right_leg.knee,
            *frame.right_leg.ankle,
            *frame.right_leg.foot,
        ]
        keypoints_msg.data = keypoints
        self.leg_keypoints_publisher.publish(keypoints_msg)

        self.get_logger().debug(
            f"Gait metrics: stride={metrics.stride_length_mm:.1f}mm, "
            f"cadence={metrics.cadence_steps_per_min:.1f} steps/min, "
            f"symmetry={metrics.symmetry_index:.2f}, "
            f"stability={metrics.stability_index:.2f}"
        )


def main(args=None):
    """Main entry point."""
    rclpy.init(args=args)
    node = GaitAnalyzerNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
