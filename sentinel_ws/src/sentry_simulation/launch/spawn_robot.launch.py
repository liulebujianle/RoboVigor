"""Spawn the sentry and publish its description and world transform for RViz."""

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """Use the same URDF for Gazebo and RViz."""
    # 从安装目录读取模型，避免依赖当前终端所在目录。
    model_file = (
        Path(get_package_share_directory('sentry_simulation'))
        / 'urdf' / 'sentry_simple.urdf'
    )

    return LaunchDescription([
        # 临时生成位置：z 是车体中心高度，不是车底高度。
        # 平面运动插件会设置竖直速度为零；高度需接近支撑面加半高。
        DeclareLaunchArgument('x', default_value='1.25'),
        DeclareLaunchArgument('y', default_value='6.75'),
        DeclareLaunchArgument('z', default_value='0.113'),
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{
                'robot_description': model_file.read_text(),
                'use_sim_time': True,
            }],
            output='screen',
        ),
        # planar_move publishes Gazebo world poses as odom coordinates.
        # Keep the two frames coincident; do not apply the spawn offset twice.
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            arguments=[
                '--frame-id', 'world', '--child-frame-id', 'odom',
                '--x', '0', '--y', '0', '--z', '0',
            ],
            output='screen',
        ),
        Node(
            package='gazebo_ros',
            executable='spawn_entity.py',
            output='screen',
            arguments=[
                '-entity', 'robovigor_sentry_simple',
                '-file', str(model_file),
                '-x', LaunchConfiguration('x'),
                '-y', LaunchConfiguration('y'),
                '-z', LaunchConfiguration('z'),
                # 场地模型较大，允许等待服务最多 120 秒。
                '-timeout', '120.0',
            ],
        ),
    ])
