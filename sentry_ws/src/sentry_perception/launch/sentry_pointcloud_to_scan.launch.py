"""将指定高度范围内的点云转换为二维 /scan。"""

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    """支持仿真和厂家点云话题，点云坐标系到 target_frame 的 TF 需有效。"""
    share = Path(get_package_share_directory('sentry_perception'))
    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('cloud_topic', default_value='/lidar/points'),
        DeclareLaunchArgument('target_frame', default_value='base_link'),
        Node(
            package='pointcloud_to_laserscan',
            executable='pointcloud_to_laserscan_node',
            name='pointcloud_to_laserscan',
            parameters=[str(share / 'config/sentry_pointcloud_to_scan.yaml'),
                        {'use_sim_time': ParameterValue(LaunchConfiguration('use_sim_time'), value_type=bool),
                         'target_frame': LaunchConfiguration('target_frame')}],
            remappings=[('cloud_in', LaunchConfiguration('cloud_topic')), ('scan', '/scan')],
            output='screen'),
    ])
