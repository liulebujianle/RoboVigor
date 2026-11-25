"""检查默认几何模型、离地间隙和刚体惯量。"""
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
import xacro

PACKAGE = Path(__file__).resolve().parents[1]


def model():
    """展开 RViz 和 Gazebo 使用的机器人模型。"""
    return ET.fromstring(xacro.process_file(str(PACKAGE / 'urdf/sentry.urdf.xacro')).toxml())


def test_gimbal_is_a_separate_articulated_visual():
    """转台网格位于自己的旋转关节上，两台雷达各有安装坐标系。"""
    robot = model()
    joint = robot.find("joint[@name='gimbal_yaw_joint']")
    assert joint.get('type') == 'continuous'
    assert joint.find('parent').get('link') == 'chassis_link'
    assert joint.find('child').get('link') == 'gimbal_yaw_link'
    assert np.allclose(np.fromstring(joint.find('axis').get('xyz'), sep=' '), [0, 0, 1])
    for name in ('mid360s_link', 'odin1_lite_link'):
        assert robot.find(f"link[@name='{name}']") is not None
    meshes = {
        'chassis_link': 'sentry_chassis.dae',
        'gimbal_yaw_link': 'sentry_turntable.dae',
        'mid360s_link': 'sentry_mid360s.dae',
        'odin1_lite_mount_link': 'sentry_odin1_lite.dae',
        **{f'wheel_{i}_link': f'sentry_wheel_{i}.dae' for i in range(1, 5)},
    }
    for link, filename in meshes.items():
        mesh = robot.find(f"link[@name='{link}']/visual/geometry/mesh")
        assert mesh is not None, link
        assert mesh.get('filename') == f'package://sentry_description/meshes/navigation/{filename}'
        assert (PACKAGE / 'meshes/navigation' / filename).is_file()
    assert not (PACKAGE / 'urdf/sentry_simple.urdf').exists()


def test_mid360s_visual_envelope_and_shading():
    """检查壳体的毫米尺寸，同时防止圆角退回逐面着色的方盒。"""
    path = PACKAGE / 'meshes/navigation/sentry_mid360s.dae'
    dae = ET.parse(path)
    mesh = dae.find('.//{*}mesh')
    size_scale = float(dae.find('.//{*}asset/{*}unit').get('meter'))
    assert dae.findtext('.//{*}asset/{*}up_axis') == 'Z_UP'

    def coordinates(source):
        array = mesh.find(f"{{*}}source[@id='{source[1:]}']/{{*}}float_array")
        return np.fromstring(array.text, sep=' ').reshape(-1, 3)

    position = mesh.find("{*}vertices/{*}input[@semantic='POSITION']")
    xyz = coordinates(position.get('source')) * size_scale
    np.testing.assert_allclose(np.ptp(xyz, axis=0), [.065, .065, .060], atol=1e-6)
    normal = mesh.find("{*}triangles/{*}input[@semantic='NORMAL']")
    vectors = coordinates(normal.get('source'))
    np.testing.assert_allclose(np.linalg.norm(vectors, axis=1), 1.0, atol=1e-4)
    assert len(np.unique(np.round(vectors, 2), axis=0)) > 32


def test_initial_ground_clearance():
    """检查车轮低于底盘碰撞盒，初始位置留有轮地间隙。"""
    robot = model()
    wheel = robot.find("joint[@name='wheel_1_joint']/origin")
    bottom = float(wheel.get('xyz').split()[2]) - .0761
    clearance = .118 + bottom - .003
    assert .001 <= clearance <= .005
    collision = robot.find("link[@name='chassis_link']/collision")
    origin = collision.find('origin')
    collision_z = float(origin.get('xyz', '0 0 0').split()[2]) if origin is not None else 0.
    height = float(collision.find('geometry/box').get('size').split()[2])
    assert collision_z - height / 2 > bottom + .03


def test_physical_wheel_tree_and_inertias():
    """四个驱动轮与转台具有独立关节、正质量和物理可行的惯量。"""
    robot = model()
    moving = [joint for joint in robot.findall('joint') if joint.get('type') != 'fixed']
    assert {joint.get('name') for joint in moving} == {
        'gimbal_yaw_joint', 'small_yaw_joint', *(f'wheel_{i}_joint' for i in range(1, 5)),
    }
    assert all(joint.get('type') == 'continuous' for joint in moving)
    for joint in moving:
        name = joint.find('child').get('link')
        assert robot.find(f"link[@name='{name}']/inertial") is not None
    assert not any(e.get('name', '').startswith('roller_') for e in robot)
    assert len(robot.findall('.//collision/geometry/cylinder')) == 4
    assert not robot.findall('gazebo')
    for link in robot.findall('link'):
        inertial = link.find('inertial')
        if inertial is None:
            continue
        assert float(inertial.find('mass').get('value')) > 0
        i = inertial.find('inertia')
        tensor = np.array([[float(i.get('ixx')), float(i.get('ixy')), float(i.get('ixz'))],
                           [float(i.get('ixy')), float(i.get('iyy')), float(i.get('iyz'))],
                           [float(i.get('ixz')), float(i.get('iyz')), float(i.get('izz'))]])
        values = np.linalg.eigvalsh(tensor)
        assert np.all(values > 0)
        assert values[-1] <= values[0] + values[1] + 1e-10
