"""把 /lidar/points（3D 点云）压成一条固定高度的 /scan 给导航用。"""

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """话题名和高度带都在 config/pointcloud_to_scan.yaml 里。"""
    share = Path(get_package_share_directory('sentry_perception'))
    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        Node(
            package='pointcloud_to_laserscan',
            executable='pointcloud_to_laserscan_node',
            name='pointcloud_to_laserscan',
            parameters=[str(share / 'config/pointcloud_to_scan.yaml'),
                        {'use_sim_time': LaunchConfiguration('use_sim_time')}],
            remappings=[('cloud_in', '/lidar/points'), ('scan', '/scan')],
            output='screen'),
    ])
