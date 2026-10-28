"""Launch the field, robot, Gazebo, RViz and keyboard control together."""

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    sim_dir = Path(get_package_share_directory('sentry_simulation'))
    arena_dir = Path(get_package_share_directory('rm_arena'))
    return LaunchDescription([
        DeclareLaunchArgument('rviz', default_value='true'),
        DeclareLaunchArgument('x', default_value='1.25'),
        DeclareLaunchArgument('y', default_value='6.75'),
        DeclareLaunchArgument('z', default_value='0.113'),
        # 继续复用用户已有的场地启动文件。
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(arena_dir / 'launch/simulation.launch.py')),
            launch_arguments={'gazebo': 'true', 'rviz': LaunchConfiguration('rviz')}.items(),
        ),
        # spawn_entity 会等待 Gazebo 服务，不使用固定延时猜测启动时间。
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(sim_dir / 'launch/spawn_robot.launch.py')),
            launch_arguments={axis: LaunchConfiguration(axis) for axis in ('x', 'y', 'z')}.items(),
        ),
        Node(package='sentry_simulation', executable='keyboard_control.py', output='screen'),
        # --wait 使 launch 跟踪新窗口中的命令；执行参数无需经过 shell 拼接。
        ExecuteProcess(
            cmd=['gnome-terminal', '--wait', '--title=RoboVigor WASD', '--',
                 'ros2', 'run', 'sentry_simulation', 'keyboard_control.py', '--keyboard'],
            output='screen',
        ),
    ])
