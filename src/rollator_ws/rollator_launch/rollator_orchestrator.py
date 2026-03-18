"""
Smart Rollator System Orchestrator
Coordinates sensor, motor, and gait modules
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from std_msgs.msg import String, Float32
from geometry_msgs.msg import Twist
from sensor_msgs.msg import PointCloud2
import time


class RollatorOrchestrator(Node):
    """
    System orchestrator for Smart Rollator.
    Coordinates all modules and provides high-level control.
    """

    def __init__(self):
        super().__init__("rollator_orchestrator")

        # Declare parameters
        self.declare_parameter("system_state", "idle")  # idle, walking, stopped
        self.declare_parameter("max_velocity", 1.0)
        self.declare_parameter("safety_enabled", True)

        self.system_state = self.get_parameter("system_state").value
        self.max_velocity = self.get_parameter("max_velocity").value
        self.safety_enabled = self.get_parameter("safety_enabled").value

        # QoS
        qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            depth=5,
        )

        # Publishers
        self.cmd_vel_pub = self.create_publisher(Twist, "cmd_vel", 10)
        self.system_status_pub = self.create_publisher(String, "system/status", 10)
        self.heartbeat_pub = self.create_publisher(Float32, "system/heartbeat", 10)

        # Subscribers
        self.gait_metrics_sub = self.create_subscription(
            String, "gait/phase", self.gait_callback, qos
        )
        self.motor_state_sub = self.create_subscription(
            String, "motor_state", self.motor_callback, qos
        )

        # Timer for system monitoring
        self.timer = self.create_timer(1.0, self.system_monitor_callback)

        self.get_logger().info("RollatorOrchestrator initialized")

    def gait_callback(self, msg: String):
        """Callback for gait phase updates."""
        try:
            phase = msg.data
            self.get_logger().debug(f"Gait phase: {phase}")

            # Adjust motor commands based on gait phase
            if self.system_state == "walking":
                self.adjust_motor_velocity(phase)

        except Exception as e:
            self.get_logger().error(f"Error in gait_callback: {e}")

    def motor_callback(self, msg: String):
        """Callback for motor state updates."""
        try:
            self.get_logger().debug(f"Motor state: {msg.data}")

            # Check for motor faults
            if "error" in msg.data.lower() or "fault" in msg.data.lower():
                self.handle_motor_fault()

        except Exception as e:
            self.get_logger().error(f"Error in motor_callback: {e}")

    def adjust_motor_velocity(self, gait_phase: str):
        """Adjust motor velocity based on gait phase."""
        try:
            cmd = Twist()

            if "STANCE" in gait_phase:
                # Stable phase - maintain velocity
                cmd.linear.x = self.max_velocity
            elif "SWING" in gait_phase:
                # Swing phase - slight velocity reduction for stability
                cmd.linear.x = self.max_velocity * 0.9

            self.cmd_vel_pub.publish(cmd)

        except Exception as e:
            self.get_logger().error(f"Error adjusting velocity: {e}")

    def system_monitor_callback(self):
        """Monitor system health."""
        try:
            # Send heartbeat
            heartbeat = Float32()
            heartbeat.data = float(time.time())
            self.heartbeat_pub.publish(heartbeat)

            # Update status
            status = String()
            status.data = f"state:{self.system_state}, velocity:{self.max_velocity:.2f}"
            self.system_status_pub.publish(status)

        except Exception as e:
            self.get_logger().error(f"Error in system monitor: {e}")

    def handle_motor_fault(self):
        """Handle motor fault - stop immediately."""
        try:
            self.get_logger().warn("Motor fault detected - stopping immediately")

            # Send stop command
            cmd = Twist()
            self.cmd_vel_pub.publish(cmd)

            self.system_state = "stopped"

            # Publish alert
            status = String()
            status.data = "MOTOR_FAULT"
            self.system_status_pub.publish(status)

        except Exception as e:
            self.get_logger().error(f"Error handling motor fault: {e}")

    def start_walking(self, velocity: float = None):
        """Start the rollator walking."""
        try:
            if velocity is None:
                velocity = self.max_velocity

            velocity = min(velocity, self.max_velocity)
            self.system_state = "walking"

            self.get_logger().info(f"Starting walk at {velocity:.2f} m/s")

        except Exception as e:
            self.get_logger().error(f"Error starting walk: {e}")

    def stop(self):
        """Stop the rollator."""
        try:
            self.get_logger().info("Stopping rollator")

            cmd = Twist()
            self.cmd_vel_pub.publish(cmd)

            self.system_state = "stopped"

        except Exception as e:
            self.get_logger().error(f"Error stopping: {e}")


def main(args=None):
    """Main entry point."""
    rclpy.init(args=args)
    node = RollatorOrchestrator()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
