"""启动 Gazebo 仿真和导航 RViz 预览。"""

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    sim_share = Path(get_package_share_directory('sentry_sim'))
    bringup_share = Path(get_package_share_directory('sentry_bringup'))
    sim_launch = sim_share / 'launch' / 'sentry_sim.launch.py'
    rviz_config = bringup_share / 'rviz' / 'sentry_navigation.rviz'

    simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(str(sim_launch)),
        launch_arguments={
            'gazebo': 'true',
            'gui': LaunchConfiguration('gui'),
            'rviz': LaunchConfiguration('rviz'),
            'rviz_config': str(rviz_config),
        }.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument('gui', default_value='true'),
        DeclareLaunchArgument('rviz', default_value='true'),
        simulation,
    ])
