"""起 Qt 键盘窗口，窗口与速度看门狗在同一个进程里。"""
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """唯一入口：keyboard_control.py（窗口 + 同进程看门狗）。"""
    share = Path(get_package_share_directory('sentry_motion'))
    return LaunchDescription([
        DeclareLaunchArgument('keyboard', default_value='true'),
        DeclareLaunchArgument('linear_speed', default_value='0.8'),
        DeclareLaunchArgument('angular_speed', default_value='1.5'),
        DeclareLaunchArgument('spin_speed', default_value='3.0'),
        Node(
            package='sentry_motion', executable='keyboard_control.py',
            parameters=[str(share / 'config/velocity_mux.yaml')],
            arguments=['--linear', LaunchConfiguration('linear_speed'),
                       '--angular', LaunchConfiguration('angular_speed'),
                       '--spin-speed', LaunchConfiguration('spin_speed')],
            condition=IfCondition(LaunchConfiguration('keyboard')), output='screen'),
    ])
