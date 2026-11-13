"""Real Odin1 Lite entry point. Requires separately installed official v3.x driver."""
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def start_driver(context):
    try:
        share = Path(get_package_share_directory('odin_ros_driver_rev1'))
    except LookupError as error:
        raise RuntimeError('Install/source the official Odin1 Lite driver first; see sentry_perception/README.md') from error
    return [IncludeLaunchDescription(
        PythonLaunchDescriptionSource(str(share / 'launch/odin1Lite.launch.py')),
        launch_arguments={key: LaunchConfiguration(key) for key in (
            'start_rviz', 'topic_prefix', 'raw_frame_id', 'tf_publish_rate')}.items())]


def generate_launch_description():
    share = Path(get_package_share_directory('sentry_perception'))
    return LaunchDescription([
        DeclareLaunchArgument('start_rviz', default_value='true'),
        DeclareLaunchArgument('topic_prefix', default_value='manifold'),
        DeclareLaunchArgument('device_index', default_value='0'),
        # Do not rename the native frame to an uncalibrated robot mount frame.
        DeclareLaunchArgument('raw_frame_id', default_value='lidar'),
        DeclareLaunchArgument('tf_publish_rate', default_value='50'),
        DeclareLaunchArgument('perception', default_value='false',
                              description='Enable /scan after validating TF and slicing heights'),
        DeclareLaunchArgument('target_frame', default_value='base_link'),
        DeclareLaunchArgument('cloud_topic', default_value=[
            '/', LaunchConfiguration('topic_prefix'), '/device',
            LaunchConfiguration('device_index'), '/cloud/raw']),
        OpaqueFunction(function=start_driver),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(share / 'launch/pointcloud_to_scan.launch.py')),
            launch_arguments={'use_sim_time': 'false',
                              'cloud_topic': LaunchConfiguration('cloud_topic'),
                              'target_frame': LaunchConfiguration('target_frame')}.items(),
            condition=IfCondition(LaunchConfiguration('perception'))),
    ])
