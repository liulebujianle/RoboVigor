"""Recover the supplied CAD's driven hubs and passive omni-wheel rollers."""

import math
import xml.etree.ElementTree as ET

import numpy as np


def rolling_rate(axis, center, radius, twist):
    """Positive axle speed rolls the chassis along axle cross world-up."""
    ax, ay, _ = axis
    x, y, _ = center
    vx, vy, wz = twist
    return (ay * (vx - wz * y) - ax * (vy + wz * x)) / radius


def origin(element):
    matrix = np.eye(4)
    if element is None:
        return matrix
    a, b, c = map(float, element.get('rpy', '0 0 0').split())
    ca, sa, cb, sb, cc, sc = math.cos(a), math.sin(a), math.cos(b), math.sin(b), math.cos(c), math.sin(c)
    matrix[:3, :3] = [[cc*cb, cc*sb*sa-sc*ca, cc*sb*ca+sc*sa],
                     [sc*cb, sc*sb*sa+cc*ca, sc*sb*ca-cc*sa], [-sb, cb*sa, cb*ca]]
    matrix[:3, 3] = list(map(float, element.get('xyz', '0 0 0').split()))
    return matrix


def recover(parts, reference):
    """Match rubber instances to original axes, leaving stators/brackets fixed."""
    robot = ET.parse(reference).getroot()
    joints = {joint.find('child').get('link'): joint for joint in robot.findall('joint')}
    poses = {'base_link': np.eye(4)}

    def pose(name):
        if name not in poses:
            joint = joints[name]
            poses[name] = pose(joint.find('parent').get('link')) @ origin(joint.find('origin'))
        return poses[name]

    conversion = np.eye(4)
    conversion[:3, :3] = [[1, 0, 0], [0, 0, -1], [0, 1, 0]]
    matrices = np.array([conversion @ np.array(p.transform).reshape(4, 4).T for p in parts])
    roles, specs, modules = {}, {}, {}
    for link in robot.findall('link'):
        name = link.get('name')
        if not name.startswith('roller_'):
            continue
        expected = pose(name) @ origin(link.find('visual/origin'))
        matches = np.flatnonzero(np.max(np.abs(matrices - expected), axis=(1, 2)) < 1e-7)
        if len(matches) != 1:
            raise RuntimeError(f'{name}: expected one native rubber instance, found {len(matches)}')
        component = parts[matches[0]]
        joint = joints[name]
        parent = joint.find('parent').get('link')
        module = component.name.split('/')[1].split('@')[0]
        if module in modules and modules[module] != parent:
            raise RuntimeError('Native wheel module is not attached to a unique axle')
        modules[module] = parent
        axis = np.array(list(map(float, joint.find('axis').get('xyz').split())))
        axis /= np.linalg.norm(axis)
        position = pose(name)[:3, 3]
        v = np.asarray(component.mesh.vertices)[:, [0, 2, 1]] * [0.001, -0.001, 0.001] - position
        axial = v @ axis
        center = axis * (axial.min() + axial.max()) / 2
        radius = np.linalg.norm(v - np.outer(axial, axis), axis=1).max()
        roles[component.name] = name
        specs[name] = dict(parent=parent, position=position.tolist(), axis=axis.tolist(),
                           center=center.tolist(), radius=float(radius),
                           origin=origin(joint.find('origin'))[:3, 3].tolist())
    for i in range(1, 5):
        name = f'wheel_{i}_link'
        joint = joints[name]
        axis = np.array(list(map(float, joint.find('axis').get('xyz').split())))
        axis[abs(axis) < 1e-10] = 0
        axis /= np.linalg.norm(axis)
        position = pose(name)[:3, 3]
        children = [spec for spec in specs.values() if spec['parent'] == name]
        if len(children) != 28:
            raise RuntimeError(f'{name}: expected 28 passive rollers')
        radii = []
        for child in children:
            center = np.array(child['position']) + child['center'] - position
            radii.append(np.linalg.norm(center - np.dot(center, axis)*axis) + child['radius'])
        specs[name] = dict(parent='chassis_link', position=position.tolist(), origin=position.tolist(),
                           axis=axis.tolist(), radius=float(np.mean(radii)))
    for component in parts:
        if component.name in roles or not component.name.startswith('底盘总装-'):
            continue
        segments = component.name.split('/')
        # Only the actual rotating inner wheel assembly. Motors, suspension,
        # slides and brackets outside it stay in the rigid chassis visual.
        if any('哨兵轮组-全向轮装配-' in segment for segment in segments):
            module = segments[1].split('@')[0]
            roles[component.name] = modules[module]
    return roles, specs


def vector(values):
    return ' '.join(f'{float(value):.12g}' for value in values)


def add_physics(robot, specs):
    """Add torque-driven hubs, free rubber rollers and their contact shapes."""
    chassis = robot.find("link[@name='chassis_link']")
    chassis.find('collision/origin').set('xyz', '0 0 0')
    chassis.find('collision/geometry/box').set('size', '0.30 0.30 0.08')
    chassis.find('inertial/mass').set('value', '6.5')
    inertia = chassis.find('inertial/inertia')
    inertia.set('ixx', '0.179616667')
    inertia.set('iyy', '0.179616667')
    inertia.set('izz', '0.3159')
    # Find the model-level gazebo block rather than reference material blocks.
    plugins = next(g for g in robot.findall('gazebo') if g.get('reference') is None)
    for plugin in list(plugins.findall('plugin')):
        if plugin.get('name') == 'sentry_planar_move':
            plugins.remove(plugin)
    drive = ET.SubElement(plugins, 'plugin', name='sentry_omni_drive', filename='libsentry_omni_drive.so')
    ET.SubElement(ET.SubElement(drive, 'ros'), 'namespace').text = '/'
    for name, spec in specs.items():
        is_wheel = name.startswith('wheel_')
        link = ET.SubElement(robot, 'link', name=name)
        visual = ET.SubElement(link, 'visual')
        geometry = ET.SubElement(visual, 'geometry')
        ET.SubElement(geometry, 'mesh', filename=f'package://sentry_description/meshes/{name}.stl')
        ET.SubElement(visual, 'material', name='cad_gray')
        inertial = ET.SubElement(link, 'inertial')
        mass = 0.25 if is_wheel else 0.5 / 112
        ET.SubElement(inertial, 'mass', value=f'{mass:.12g}')
        collision = ET.SubElement(link, 'collision')
        geometry = ET.SubElement(collision, 'geometry')
        if is_wheel:
            radius, length = 0.05, 0.04
            axis = np.array(spec['axis'])
            parallel = mass * radius**2 / 2
            perpendicular = mass * (3*radius**2 + length**2) / 12
            tensor = perpendicular*np.eye(3) + (parallel-perpendicular)*np.outer(axis, axis)
            ET.SubElement(collision, 'origin', xyz='0 0 0', rpy=f'0 {math.pi/2} {math.atan2(axis[1],axis[0])}')
            ET.SubElement(geometry, 'cylinder', radius=str(radius), length=str(length))
            params = ET.SubElement(drive, 'wheel', joint=name.replace('_link', '_joint'))
            ET.SubElement(params, 'radius').text = str(spec['radius'])
        else:
            ET.SubElement(inertial, 'origin', xyz=vector(spec['center']))
            ET.SubElement(collision, 'origin', xyz=vector(spec['center']))
            ET.SubElement(geometry, 'sphere', radius=str(spec['radius']))
            tensor = np.eye(3) * 0.4 * mass * spec['radius']**2
        ET.SubElement(inertial, 'inertia', **{
            key: f'{tensor[i,j]:.12g}' for key,i,j in
            [('ixx',0,0),('iyy',1,1),('izz',2,2),('ixy',0,1),('ixz',0,2),('iyz',1,2)]})
        joint = ET.SubElement(robot, 'joint', name=name.replace('_link', '_joint'), type='continuous')
        ET.SubElement(joint, 'parent', link=spec['parent'])
        ET.SubElement(joint, 'child', link=name)
        ET.SubElement(joint, 'origin', xyz=vector(spec['origin']))
        ET.SubElement(joint, 'axis', xyz=vector(spec['axis']))
        ET.SubElement(joint, 'limit', effort='1.2' if is_wheel else '0.1', velocity='1000')
        ET.SubElement(joint, 'dynamics', damping='0.0001' if is_wheel else '0.000001', friction='0')
        gazebo = ET.SubElement(robot, 'gazebo', reference=name)
        ET.SubElement(gazebo, 'material').text = 'Gazebo/Grey'
        if not is_wheel:
            for key, value in [('mu1','0.9'),('mu2','0.9'),('kp','100000'),('kd','100'),
                               ('minDepth','0.00005'),('maxVel','0.1'),('maxContacts','3')]:
                ET.SubElement(gazebo, key).text = value
