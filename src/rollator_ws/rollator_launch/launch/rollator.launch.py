"""
Smart Rollator main launch file
Launches all nodes: sensor, motor controller, and gait analyzer
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    """Generate launch description for Smart Rollator."""

    # Declare launch arguments
    camera_index_arg = DeclareLaunchArgument(
        "camera_index",
        default_value="0",
        description="Camera device index"
    )

    motor_port_arg = DeclareLaunchArgument(
        "motor_port",
        default_value="/dev/ttyUSB0",
        description="Motor controller serial port"
    )

    publish_rate_arg = DeclareLaunchArgument(
        "publish_rate",
        default_value="30",
        description="Publishing rate in Hz"
    )

    # Arducam sensor node
    arducam_node = Node(
        package="rollator_sensor",
        executable="arducam_node",
        name="arducam_node",
        parameters=[
            {"camera_index": LaunchConfiguration("camera_index")},
            {"frame_width": 640},
            {"frame_height": 480},
            {"publish_rate": LaunchConfiguration("publish_rate")},
            {"frame_id": "camera_depth"},
        ],
        output="screen",
    )

    # Motor controller node
    motor_node = Node(
        package="rollator_motor",
        executable="motor_controller_node",
        name="motor_controller_node",
        parameters=[
            {"serial_port": LaunchConfiguration("motor_port")},
            {"baudrate": 115200},
            {"max_velocity": 1.0},
            {"publish_rate": 10},
        ],
        output="screen",
    )

    # Gait analyzer node
    gait_node = Node(
        package="rollator_gait",
        executable="gait_analyzer_node",
        name="gait_analyzer_node",
        parameters=[
            {"history_size": 30},
            {"sampling_rate": LaunchConfiguration("publish_rate")},
            {"legs_roi_top": 0.3},
        ],
        output="screen",
    )

    # Create launch description
    return LaunchDescription([
        camera_index_arg,
        motor_port_arg,
        publish_rate_arg,
        LogInfo(msg="Starting Smart Rollator system..."),
        arducam_node,
        motor_node,
        gait_node,
    ])
