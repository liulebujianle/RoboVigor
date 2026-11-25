"""分别导出车体 Xacro 和 Gazebo 仿真配置。"""
from copy import deepcopy
from pathlib import Path
import xml.etree.ElementTree as ET


def write_model(robot, description, simulation):
    """按底盘、云台、仿真拆分文件，保留原有连杆和关节。"""
    description, simulation = Path(description), Path(simulation)
    for folder in (description / 'urdf', simulation / 'urdf'):
        folder.mkdir(parents=True, exist_ok=True)
    robot = deepcopy(robot)
    legacy_prefix = 'package://sentry_simulation/'
    legacy_names = {'meshes/sentry_chassis.stl': 'meshes/chassis.stl',
                    'meshes/sentry_gimbal.stl': 'meshes/gimbal.stl'}
    for mesh in robot.findall('.//mesh'):
        uri = mesh.get('filename')
        if uri.startswith(legacy_prefix):
            path = uri[len(legacy_prefix):]
            mesh.set('filename', 'package://sentry_description/' + legacy_names.get(path, path))
    chassis, gimbal, gazebo = [], [], []
    for element in robot:
        if element.tag == 'gazebo':
            gazebo.append(element)
        elif element.get('name') in ('gimbal_yaw_link', 'gimbal_yaw_joint', 'small_yaw_link', 'small_yaw_joint'):
            gimbal.append(element)
        else:
            chassis.append(element)

    def fragment(path, elements):
        tree = ET.Element('robot', {'xmlns:xacro': 'http://www.ros.org/wiki/xacro'})
        for element in elements:
            tree.append(element)
        ET.indent(tree, space='  ')
        ET.ElementTree(tree).write(path, encoding='utf-8', xml_declaration=True)

    fragment(description / 'urdf/chassis.xacro', chassis)
    fragment(description / 'urdf/gimbal.xacro', gimbal)
    sensors = description / 'urdf/sensors.xacro'
    if not sensors.exists():
        sensors.write_text('''<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro">
  <!-- 传感器外参尚未标定；这里只保留 CAD 外形，不发布雷达或 IMU 数据。 -->
</robot>
''')
    (description / 'urdf/sentry.urdf.xacro').write_text('''<?xml version="1.0"?>
<robot name="robovigor_sentry" xmlns:xacro="http://www.ros.org/wiki/xacro">
  <xacro:include filename="chassis.xacro"/>
  <xacro:include filename="gimbal.xacro"/>
  <xacro:include filename="sensors.xacro"/>
</robot>
''')
    tree = ET.Element('robot', name='robovigor_sentry', **{'xmlns:xacro': 'http://www.ros.org/wiki/xacro'})
    ET.SubElement(tree, 'xacro:include', filename='$(find sentry_description)/urdf/sentry.urdf.xacro')
    for element in gazebo:
        tree.append(element)
    ET.indent(tree, space='  ')
    ET.ElementTree(tree).write(simulation / 'urdf/sentry_sim.urdf.xacro', encoding='utf-8', xml_declaration=True)
