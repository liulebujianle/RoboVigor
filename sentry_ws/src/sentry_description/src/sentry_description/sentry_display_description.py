"""从物理模型生成用于显示和 TF 发布的模型。"""
from copy import deepcopy
import math
import xml.etree.ElementTree as ET

import numpy as np


def origin(element):
    """将 URDF origin 转成从子坐标系到父坐标系的齐次矩阵。"""
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


def display_description(description, *, show_small_yaw_marker=False):
    """把滚子几何合并到车轮，每个车轮只保留一个转轴坐标系。"""
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
    # 枪管参考系沿用上装网格的原点。
    frame_name = 'barrel_mesh_frame'
    for visual in robot.findall("link[@name='gimbal_yaw_link']/visual"):
        mesh = visual.find('geometry/mesh')
        if mesh is None or not mesh.get('filename', '').endswith('/sentry_turntable.dae'):
            continue
        if frame_name not in links:
            ET.SubElement(robot, 'link', name=frame_name)
            joint = ET.SubElement(robot, 'joint', name=frame_name + '_fixed', type='fixed')
            ET.SubElement(joint, 'parent', link='gimbal_yaw_link')
            ET.SubElement(joint, 'child', link=frame_name)
            frame_origin = deepcopy(visual.find('origin'))
            if frame_origin is not None:
                joint.append(frame_origin)
        break
    # GUI 预览用一个偏心色点显示小轴转角。点只存在于 RViz 显示模型。
    if show_small_yaw_marker and 'small_yaw_link' in links:
        marker = ET.SubElement(links['small_yaw_link'], 'visual', name='small_yaw_indicator')
        ET.SubElement(marker, 'origin', xyz='0.08 0 0.38')
        ET.SubElement(ET.SubElement(marker, 'geometry'), 'sphere', radius='0.012')
        yellow = ET.SubElement(marker, 'material', name='small_yaw_yellow')
        ET.SubElement(yellow, 'color', rgba='1.0 0.8 0.0 1.0')
    return ET.tostring(robot, encoding='unicode')


