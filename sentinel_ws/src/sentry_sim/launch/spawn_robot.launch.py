"""Spawn the sentry and publish its description and world transform for RViz."""

from pathlib import Path
import xml.etree.ElementTree as ET
import xacro
import yaml

from ament_index_python.packages import get_package_prefix, get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """Use the same URDF for Gazebo and RViz."""
    # 从安装目录读取模型，避免依赖当前终端所在目录。
    model_file = (
        Path(get_package_share_directory('sentry_sim'))
        / 'urdf' / 'sentry_sim.urdf.xacro'
    )
    description_share = Path(get_package_share_directory('sentry_description'))
    config = yaml.safe_load((model_file.parents[1] / 'config/simulation.yaml').read_text())
    robot = ET.fromstring(xacro.process_file(str(model_file)).toxml())
    for mesh in robot.findall('.//mesh'):
        uri = mesh.get('filename')
        package, relative = uri.removeprefix('package://').split('/', 1)
        path = Path(get_package_share_directory(package)) / relative
        if not path.is_file():
            raise FileNotFoundError(f'Robot mesh is missing: {path}')
        mesh.set('filename', path.as_uri())
    for plugin in robot.findall('.//plugin'):
        if plugin.get('filename') in ('libsentry_gimbal_stabilizer.so', 'libsentry_omni_drive.so'):
            library = (Path(get_package_prefix('sentry_sim')) / 'lib'
                       / plugin.get('filename'))
            if not library.is_file():
                raise FileNotFoundError(f'Build sentry_sim before launch: {library}')
            plugin.set('filename', str(library))
    description = ET.tostring(robot, encoding='unicode')

    return LaunchDescription([
        # 临时生成位置：z 是车体中心高度，不是车底高度。
        # 轮地物理会在重力作用下让车辆落在实际支撑面。
        DeclareLaunchArgument('x', default_value=str(config['spawn']['x'])),
        DeclareLaunchArgument('y', default_value=str(config['spawn']['y'])),
        DeclareLaunchArgument('z', default_value=str(config['spawn']['z'])),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(description_share / 'launch/description.launch.py')),
            launch_arguments={'robot_description': description, 'use_sim_time': 'true'}.items(),
        ),
        # Torque drive publishes Gazebo world poses as odom coordinates.
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
                '-entity', config['entity'],
                '-topic', '/sentry_description/robot_description_physics',
                '-x', LaunchConfiguration('x'),
                '-y', LaunchConfiguration('y'),
                '-z', LaunchConfiguration('z'),
                # 场地模型较大，允许等待服务最多 120 秒。
                '-timeout', '120.0',
            ],
        ),
    ])
