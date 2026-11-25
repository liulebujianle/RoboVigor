"""生成 Gazebo 机器人，发布模型描述和 RViz 所需的世界坐标变换。"""

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
    """Gazebo 和 RViz 共用同一份 URDF。"""
    # 从安装目录读取模型，避免依赖当前终端所在目录。
    model_file = (
        Path(get_package_share_directory('sentry_sim'))
        / 'urdf' / 'sentry_sim.urdf.xacro'
    )
    description_share = Path(get_package_share_directory('sentry_description'))
    config = yaml.safe_load((model_file.parents[1] / 'config/sentry_simulation.yaml').read_text())
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
        # z 表示车体中心高度。
        # 机器人生成后在重力作用下落到支撑面。
        DeclareLaunchArgument('x', default_value=str(config['spawn']['x'])),
        DeclareLaunchArgument('y', default_value=str(config['spawn']['y'])),
        DeclareLaunchArgument('z', default_value=str(config['spawn']['z'])),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(description_share / 'launch/sentry_description.launch.py')),
            # 场地和 RViz 由 sentry_sim.launch.py 启动，避免重复发布 /arena_marker。
            launch_arguments={'robot_description': description, 'use_sim_time': 'true',
                              'arena': 'false', 'rviz': 'false', 'preview_joints': 'false'}.items(),
        ),
        # 底盘插件的 odom 位姿直接使用 Gazebo 世界坐标。
        # world 与 odom 重合，出生点偏移只应用一次。
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
