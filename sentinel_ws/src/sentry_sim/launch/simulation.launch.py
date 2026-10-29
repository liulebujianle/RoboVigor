"""Show the user's CAD robot in the RMUL field with Gazebo and RViz."""

import yaml
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    """Start one field and one robot, without requiring a keyboard terminal."""
    sim = Path(get_package_share_directory('sentry_sim'))
    arena = Path(get_package_share_directory('rm_arena'))
    config = yaml.safe_load((sim / 'config/simulation.yaml').read_text())
    return LaunchDescription([
        DeclareLaunchArgument('rviz_config', default_value=str(arena / 'rviz/arena.rviz')),
        DeclareLaunchArgument('gui', default_value='true'),
        DeclareLaunchArgument('rviz', default_value='true'),
        DeclareLaunchArgument('x', default_value=str(config['spawn']['x'])),
        DeclareLaunchArgument('y', default_value=str(config['spawn']['y'])),
        DeclareLaunchArgument('z', default_value=str(config['spawn']['z'])),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(arena / 'launch/simulation.launch.py')),
            launch_arguments={
                'gazebo': 'true', 'gui': LaunchConfiguration('gui'),
                'rviz': LaunchConfiguration('rviz'),
                'rviz_config': LaunchConfiguration('rviz_config'),
                'tf_topic': '/tf',
                'tf_static_topic': '/tf_static',
            }.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(sim / 'launch/spawn_robot.launch.py')),
            launch_arguments={axis: LaunchConfiguration(axis) for axis in ('x', 'y', 'z')}.items(),
        ),
    ])
