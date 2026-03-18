"""
Smart Rollator sensor-only launch file
For testing sensor and gait analysis without motor control
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    """Generate sensor-only launch description."""

    camera_index_arg = DeclareLaunchArgument(
        "camera_index",
        default_value="0",
        description="Camera device index"
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
            {"publish_rate": 30},
            {"frame_id": "camera_depth"},
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
            {"sampling_rate": 30},
            {"legs_roi_top": 0.3},
        ],
        output="screen",
    )

    return LaunchDescription([
        camera_index_arg,
        arducam_node,
        gait_node,
    ])
