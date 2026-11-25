"""组合启动场地、机器人、RViz、普通键盘和点云转扫描。

启动命令：`ros2 launch sentry_bringup sentry_sim_teleop.launch.py`。参数包括
gazebo/gui/rviz/keyboard/perception 与出生点、三个速度。
"""
from pathlib import Path

import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    """默认值来自 config/sentry_sim.yaml + sentry_sim/config/sentry_simulation.yaml。"""
    bringup = Path(get_package_share_directory('sentry_bringup'))
    sim = Path(get_package_share_directory('sentry_sim'))
    motion = Path(get_package_share_directory('sentry_motion'))
    perception = Path(get_package_share_directory('sentry_perception'))
    defaults = yaml.safe_load((bringup / 'config/sentry_sim.yaml').read_text())
    defaults.update(yaml.safe_load((sim / 'config/sentry_simulation.yaml').read_text())['spawn'])
    return LaunchDescription([
        DeclareLaunchArgument('gazebo', default_value='true'),
        DeclareLaunchArgument('perception', default_value='true'),
        *[DeclareLaunchArgument(key, default_value=str(value).lower())
          for key, value in defaults.items()],
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(sim / 'launch/sentry_sim.launch.py')),
            launch_arguments={
                **{key: LaunchConfiguration(key)
                   for key in ('gazebo', 'gui', 'rviz', 'x', 'y', 'z')},
                'rviz_config': str(bringup / 'rviz/sentry_navigation.rviz'),
            }.items()),
        # perception:=false 时不启动点云转扫描。
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                str(perception / 'launch/sentry_pointcloud_to_scan.launch.py')),
            launch_arguments={'use_sim_time': 'true'}.items(),
            condition=IfCondition(LaunchConfiguration('perception'))),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(motion / 'launch/sentry_motion.launch.py')),
            launch_arguments={key: LaunchConfiguration(key) for key in (
                'keyboard', 'linear_speed', 'angular_speed', 'spin_speed')}.items()),
    ])
