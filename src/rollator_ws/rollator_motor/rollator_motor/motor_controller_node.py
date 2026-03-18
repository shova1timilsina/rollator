"""
Motor Controller ROS 2 Node
Wraps MotorController driver and provides ROS interfaces
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float32MultiArray, Float32
from sensor_msgs.msg import BatteryState

from .motor_driver import MotorController, MotorCommand


class MotorControllerNode(Node):
    """ROS 2 Node for motor controller."""

    def __init__(self):
        super().__init__("motor_controller_node")

        # Declare parameters
        self.declare_parameter("serial_port", "/dev/ttyUSB0")
        self.declare_parameter("baudrate", 115200)
        self.declare_parameter("max_velocity", 1.0)
        self.declare_parameter("publish_rate", 10)

        # Get parameters
        serial_port = self.get_parameter("serial_port").value
        baudrate = self.get_parameter("baudrate").value
        max_velocity = self.get_parameter("max_velocity").value
        publish_rate = self.get_parameter("publish_rate").value

        # Initialize motor controller
        self.motor_controller = MotorController(
            port=serial_port, baudrate=baudrate, max_velocity=max_velocity
        )

        if not self.motor_controller.connect():
            self.get_logger().error("Failed to connect to motor controller")
            raise RuntimeError("Motor controller connection failed")

        self.get_logger().info(f"Motor controller connected at {serial_port}")

        # Subscribers
        self.cmd_vel_subscription = self.create_subscription(
            Twist, "cmd_vel", self.cmd_vel_callback, 10
        )

        # Publishers
        self.motor_state_publisher = self.create_publisher(
            Float32MultiArray, "motor_state", 10
        )
        self.motor_current_publisher = self.create_publisher(
            Float32MultiArray, "motor_current", 10
        )
        self.temperature_publisher = self.create_publisher(
            Float32, "motor_temperature", 10
        )

        # Timer for reading state
        period = 1.0 / publish_rate
        self.timer = self.create_timer(period, self.timer_callback)

        self.get_logger().info("MotorControllerNode started")

    def cmd_vel_callback(self, msg: Twist):
        """Callback for velocity commands (Twist messages)."""
        try:
            # Extract linear and angular velocities
            linear_x = msg.linear.x  # m/s
            angular_z = msg.angular.z  # rad/s

            # Convert to differential drive commands (left and right velocities)
            # Simplified model: linear_x controls forward/backward, angular_z controls turning
            max_vel = self.motor_controller.max_velocity
            track_width = 0.4  # Distance between wheels in meters (tune for your rollator)

            # Differential drive kinematics
            left_vel = linear_x - (angular_z * track_width / 2.0)
            right_vel = linear_x + (angular_z * track_width / 2.0)

            # Send to motor controller
            self.motor_controller.set_velocity(left_vel, right_vel)

            self.get_logger().debug(
                f"Cmd_vel: linear={linear_x:.2f}, angular={angular_z:.2f} -> "
                f"left={left_vel:.2f}, right={right_vel:.2f}"
            )

        except Exception as e:
            self.get_logger().error(f"Error in cmd_vel callback: {e}")

    def timer_callback(self):
        """Timer callback to read and publish motor state."""
        try:
            state = self.motor_controller.read_state()
            if state is None:
                return

            # Publish motor velocities
            motor_state_msg = Float32MultiArray()
            motor_state_msg.data = [state.left_velocity, state.right_velocity]
            self.motor_state_publisher.publish(motor_state_msg)

            # Publish motor currents
            motor_current_msg = Float32MultiArray()
            motor_current_msg.data = [state.left_current, state.right_current]
            self.motor_current_publisher.publish(motor_current_msg)

            # Publish temperature
            temp_msg = Float32()
            temp_msg.data = state.temperature
            self.temperature_publisher.publish(temp_msg)

            self.get_logger().debug(
                f"Motor state: L={state.left_velocity:.2f} m/s, "
                f"R={state.right_velocity:.2f} m/s, T={state.temperature:.1f}°C"
            )

        except Exception as e:
            self.get_logger().error(f"Error in timer callback: {e}")

    def destroy_node(self):
        """Cleanup on node destruction."""
        if self.motor_controller:
            self.motor_controller.stop()
            self.motor_controller.disconnect()
        super().destroy_node()


def main(args=None):
    """Main entry point."""
    rclpy.init(args=args)
    node = MotorControllerNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
