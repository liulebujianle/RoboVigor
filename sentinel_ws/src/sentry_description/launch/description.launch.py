"""Publish native per-wheel TF and a separate full Gazebo physics model."""
from copy import deepcopy
import math
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
import xacro


def origin(element):
    """Read a URDF origin as a homogeneous child-to-parent matrix."""
    matrix = np.eye(4)
    if element is None:
        return matrix
    r, p, y = map(float, element.get('rpy', '0 0 0').split())
    cr, sr = math.cos(r), math.sin(r)
    cp, sp = math.cos(p), math.sin(p)
    cy, sy = math.cos(y), math.sin(y)
    matrix[:3, :3] = [[cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
                      [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
                      [-sp, cp * sr, cp * cr]]
    matrix[:3, 3] = list(map(float, element.get('xyz', '0 0 0').split()))
    return matrix


def display_description(description):
    """Keep one rotating axle frame per wheel, folding roller visuals into it."""
    robot = ET.fromstring(description)
    links = {link.get('name'): link for link in robot.findall('link')}
    joints = {j.find('child').get('link'): j for j in robot.findall('joint')}
    for name, link in links.items():
        if not name.startswith('roller_'):
            continue
        joint = joints[name]
        parent = joint.find('parent').get('link')
        if not parent.startswith('wheel_'):
            raise ValueError(f'Passive roller {name} is not attached to a wheel')
        for index, visual in enumerate(link.findall('visual') + link.findall('collision')):
            pose = origin(joint.find('origin')) @ origin(visual.find('origin'))
            copied = deepcopy(visual)
            copied.set('name', f'{name}_{visual.tag}_{index}')
            entry = copied.find('origin')
            if entry is None:
                entry = ET.Element('origin')
                copied.insert(0, entry)
            rpy = [math.atan2(pose[2, 1], pose[2, 2]),
                   math.atan2(-pose[2, 0], math.hypot(pose[0, 0], pose[1, 0])),
                   math.atan2(pose[1, 0], pose[0, 0])]
            entry.set('xyz', ' '.join(f'{v:.12g}' for v in pose[:3, 3]))
            entry.set('rpy', ' '.join(f'{v:.12g}' for v in rpy))
            links[parent].append(copied)
        robot.remove(link)
        robot.remove(joint)
    for element in list(robot):
        if element.tag == 'gazebo':
            robot.remove(element)
        elif element.tag == 'link' and element.get('name') == 'wheels_link':
            robot.remove(element)
        elif element.tag == 'joint' and element.find('child').get('link') == 'wheels_link':
            robot.remove(element)
    return ET.tostring(robot, encoding='unicode')


def enabled(context, name):
    """launch 参数按字符串比较，避免 bool 转换在 OpaqueFunction 里踩坑。"""
    return LaunchConfiguration(name).perform(context).strip().lower() in ('true', '1', 'yes')


def preview(context, sim_time):
    """场地 Marker + RViz 预览；仿真链路把 arena/rviz 都关掉，各管各的显示。"""
    actions = []
    if enabled(context, 'arena'):
        # 只有一条 latched Marker，不改 robot_description
        actions.append(Node(package='rm_arena', executable='arena_marker', output='screen'))
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
        actions.append(Node(
            package='rviz2', executable='rviz2', output='screen',
            parameters=[{'use_sim_time': sim_time}],
            arguments=['-d', LaunchConfiguration('rviz_config').perform(context)]))
    return actions


def publish(context):
    """Use actual main wheel joint states with the native public RSP tree."""
    physics = LaunchConfiguration('robot_description').perform(context)
    if not physics:
        physics = xacro.process_file(LaunchConfiguration('model').perform(context)).toxml()
    sim_time = ParameterValue(LaunchConfiguration('use_sim_time'), value_type=bool)
    nodes = [
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             parameters=[{'robot_description': ParameterValue(
                 display_description(physics), value_type=str), 'use_sim_time': sim_time}],
             output='screen'),
        Node(package='sentry_description', executable='description_publisher.py',
             parameters=[{'robot_description': ParameterValue(physics, value_type=str)}],
             output='screen'),
    ]
    return nodes + preview(context, sim_time)


def generate_launch_description():
    """Keep model resources installed and preserve the public launch arguments."""
    share = Path(get_package_share_directory('sentry_description'))
    return LaunchDescription([
        DeclareLaunchArgument('model', default_value=str(share / 'urdf/sentry.urdf.xacro')),
        DeclareLaunchArgument('robot_description', default_value=''),
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        # 默认带场地和 RViz：只启动这个 launch 就能看到“车 + 场地”
        DeclareLaunchArgument('arena', default_value='true',
                              description='Publish the rm_arena field marker'),
        DeclareLaunchArgument('rviz', default_value='true',
                              description='Open RViz with the field and the robot'),
        DeclareLaunchArgument('rviz_config',
                              default_value=str(share / 'rviz/robot_field.rviz')),
        DeclareLaunchArgument('spawn_x', default_value='1.25'),
        DeclareLaunchArgument('spawn_y', default_value='6.75'),
        DeclareLaunchArgument('spawn_z', default_value='0.118'),
        OpaqueFunction(function=publish),
    ])
