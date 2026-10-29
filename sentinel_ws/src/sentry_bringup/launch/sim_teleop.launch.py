"""整套仿真的唯一入口：场地 + 机器人 + RViz + 键盘。

用 `ros2 launch sentry_bringup sim_teleop.launch.py` 启动；所有开关都是 launch 参数：
gazebo/gui/rviz/keyboard 与出生点、三个速度。
"""
from pathlib import Path

import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    """默认值来自 config/sim.yaml + sentry_sim/config/simulation.yaml。"""
    bringup = Path(get_package_share_directory('sentry_bringup'))
    sim = Path(get_package_share_directory('sentry_sim'))
    motion = Path(get_package_share_directory('sentry_motion'))
    defaults = yaml.safe_load((bringup / 'config/sim.yaml').read_text())
    defaults.update(yaml.safe_load((sim / 'config/simulation.yaml').read_text())['spawn'])
    return LaunchDescription([
        DeclareLaunchArgument('gazebo', default_value='true'),
        *[DeclareLaunchArgument(key, default_value=str(value).lower())
          for key, value in defaults.items()],
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(sim / 'launch/simulation.launch.py')),
            launch_arguments={
                **{key: LaunchConfiguration(key)
                   for key in ('gazebo', 'gui', 'rviz', 'x', 'y', 'z')},
                'rviz_config': str(bringup / 'rviz/navigation.rviz'),
            }.items()),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(motion / 'launch/motion.launch.py')),
            launch_arguments={key: LaunchConfiguration(key) for key in (
                'keyboard', 'linear_speed', 'angular_speed', 'spin_speed')}.items()),
    ])
