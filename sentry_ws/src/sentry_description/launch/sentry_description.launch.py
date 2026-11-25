"""发布机器人 TF、显示模型和 Gazebo 物理模型描述。"""
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
import xacro

from sentry_description.sentry_display_description import display_description, origin as origin


def enabled(context, name):
    """按字符串解析 launch 开关，避免非空的 "false" 被当作真值。"""
    return LaunchConfiguration(name).perform(context).strip().lower() in ('true', '1', 'yes')


def preview(context, sim_time):
    """按开关启动场地 Marker 和 RViz；仿真组合启动时关闭此处的预览。"""
    actions = []
    if enabled(context, 'arena'):
        # 只有一条 latched Marker，不改 robot_description
        actions.append(Node(package='sentry_map', executable='sentry_arena_marker', output='screen'))
        # RViz 的 Fixed Frame 是 world：给机器人一个出生点位姿，等同仿真里的初始位置
        actions.append(Node(
            package='tf2_ros', executable='static_transform_publisher',
            arguments=[
                '--frame-id', 'world', '--child-frame-id', 'base_link',
                '--x', LaunchConfiguration('spawn_x').perform(context),
                '--y', LaunchConfiguration('spawn_y').perform(context),
                '--z', LaunchConfiguration('spawn_z').perform(context),
            ],
            parameters=[{'use_sim_time': sim_time}], output='screen'))
    if enabled(context, 'rviz'):
        angle = ParameterValue(LaunchConfiguration('pitch_preview_deg'), value_type=float)
        actions.append(Node(
            package='sentry_description', executable='sentry_pitch_preview',
            name='sentry_pitch_preview', parameters=[{'angle_deg': angle, 'use_sim_time': sim_time}],
            output='screen'))
        actions.append(Node(
            package='rviz2', executable='rviz2', output='screen',
            parameters=[{'use_sim_time': sim_time}],
            arguments=['-d', LaunchConfiguration('rviz_config').perform(context)]))
    if enabled(context, 'camera_view'):
        share = Path(get_package_share_directory('sentry_description'))
        camera_config = share / 'rviz/sentry_front_camera.rviz'
        actions.append(Node(
            package='rviz2', executable='rviz2', name='rviz_front_camera',
            parameters=[{'use_sim_time': sim_time}], arguments=['-d', str(camera_config)],
            output='screen'))
    return actions


def publish(context):
    """显示模型交给 robot_state_publisher，物理模型由独立节点发布。"""
    physics = LaunchConfiguration('robot_description').perform(context)
    if not physics:
        physics = xacro.process_file(LaunchConfiguration('model').perform(context)).toxml()
    sim_time = ParameterValue(LaunchConfiguration('use_sim_time'), value_type=bool)
    preview_joints = enabled(context, 'preview_joints')
    show_joint_gui = preview_joints and enabled(context, 'joint_gui')
    display = display_description(physics, show_small_yaw_marker=show_joint_gui)
    nodes = [
        # 独立前相机的局部坐标约定。两个坐标系共用镜头原点。
        Node(package='tf2_ros', executable='static_transform_publisher',
             name='front_camera_optical_tf',
             arguments=['--frame-id', 'front_camera_link', '--child-frame-id', 'front_camera_optical_frame',
                        '--roll', '-1.5707963267948966', '--yaw', '-1.5707963267948966'],
             parameters=[{'use_sim_time': sim_time}], output='screen'),
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             parameters=[{'robot_description': ParameterValue(display, value_type=str),
                          'use_sim_time': sim_time}],
             output='screen'),
        Node(package='sentry_description', executable='sentry_description_publisher',
             parameters=[{'robot_description': ParameterValue(physics, value_type=str)}],
             output='screen'),
    ]
    if preview_joints:
        publisher = 'joint_state_publisher_gui' if show_joint_gui else 'joint_state_publisher'
        nodes.append(Node(
            package=publisher, executable=publisher,
            parameters=[{'use_sim_time': sim_time}], output='screen'))
    return nodes + preview(context, sim_time)


def generate_launch_description():
    """声明模型路径、预览开关和初始位置参数。"""
    share = Path(get_package_share_directory('sentry_description'))
    return LaunchDescription([
        DeclareLaunchArgument('model', default_value=str(share / 'urdf/sentry.urdf.xacro')),
        DeclareLaunchArgument('robot_description', default_value=''),
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        # 默认带场地和 RViz：只启动这个 launch 就能看到“车 + 场地”
        DeclareLaunchArgument('arena', default_value='true',
                              description='Publish the sentry_map field marker'),
        DeclareLaunchArgument('rviz', default_value='true',
                              description='Open RViz with the field and the robot'),
        DeclareLaunchArgument('camera_view', default_value='false',
                              description='Open an additional RViz view in the local camera frame'),
        DeclareLaunchArgument('preview_joints', default_value=LaunchConfiguration('rviz'),
                              description='Publish joint states during standalone model preview'),
        DeclareLaunchArgument('joint_gui', default_value='false',
                              description='Show sliders for standalone joint preview'),
        DeclareLaunchArgument('pitch_preview_deg', default_value='0.0',
                              description='Inclination shown on the standalone RViz gauge in degrees'),
        DeclareLaunchArgument('rviz_config',
                              default_value=str(share / 'rviz/sentry_description.rviz')),
        DeclareLaunchArgument('spawn_x', default_value='1.25'),
        DeclareLaunchArgument('spawn_y', default_value='6.75'),
        DeclareLaunchArgument('spawn_z', default_value='0.118'),
        OpaqueFunction(function=publish),
    ])
