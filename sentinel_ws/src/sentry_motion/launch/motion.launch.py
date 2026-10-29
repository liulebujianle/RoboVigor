"""Start the current manual velocity source and independent final watchdog."""
from pathlib import Path
from uuid import uuid4
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    share = Path(get_package_share_directory('sentry_motion'))
    prefix = ['/teleop/', LaunchConfiguration('control_session')]
    return LaunchDescription([
        DeclareLaunchArgument('control_session', default_value='s_' + uuid4().hex),
        DeclareLaunchArgument('keyboard', default_value='true'),
        DeclareLaunchArgument('linear_speed', default_value='0.8'),
        DeclareLaunchArgument('angular_speed', default_value='1.5'),
        DeclareLaunchArgument('spin_speed', default_value='3.0'),
        Node(package='sentry_motion', executable='keyboard_control.py', output='screen',
             parameters=[str(share / 'config/velocity_mux.yaml'),
                         {'input_prefix': ParameterValue(prefix, value_type=str)}]),
        Node(
            package='sentry_motion', executable='keyboard_window.py',
            arguments=['--input-prefix', prefix,
                       '--linear', LaunchConfiguration('linear_speed'),
                       '--angular', LaunchConfiguration('angular_speed'),
                       '--spin-speed', LaunchConfiguration('spin_speed')],
            condition=IfCondition(LaunchConfiguration('keyboard')), output='screen'),
    ])
