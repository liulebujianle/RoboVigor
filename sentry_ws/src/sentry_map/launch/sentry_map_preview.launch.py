"""单独启动 RViz 场地预览。"""
from pathlib import Path
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    share = Path(get_package_share_directory('sentry_map'))
    return LaunchDescription([IncludeLaunchDescription(
        PythonLaunchDescriptionSource(str(share / 'launch/sentry_map.launch.py')),
        launch_arguments={'gazebo': 'false', 'rviz': 'true'}.items())])
