"""Write platform Xacros separately from Gazebo-only additions."""
from copy import deepcopy
from pathlib import Path
import xml.etree.ElementTree as ET


def write_model(robot, description, simulation):
    """Keep every physical body/joint while separating resource ownership."""
    description, simulation = Path(description), Path(simulation)
    for folder in (description / 'urdf', simulation / 'urdf'):
        folder.mkdir(parents=True, exist_ok=True)
    for mesh in robot.findall('.//mesh'):
        uri = mesh.get('filename').replace('package://sentry_simulation/', 'package://sentry_description/')
        mesh.set('filename', uri.replace('sentry_chassis.stl', 'chassis.stl').replace('sentry_gimbal.stl', 'gimbal.stl'))
    chassis, gimbal, gazebo = [], [], []
    for element in robot:
        if element.tag == 'gazebo':
            gazebo.append(deepcopy(element))
        elif element.get('name') in ('gimbal_yaw_link', 'gimbal_yaw_joint'):
            gimbal.append(deepcopy(element))
        else:
            chassis.append(deepcopy(element))

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
  <!-- No measured sensor extrinsics yet. CAD housings are visual only;
       no fictitious Mid-360S or IMU frame/measurement is published. -->
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
