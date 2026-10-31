"""Guard the requested package boundaries and preserved physical robot."""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET
import xacro

WS = Path(__file__).resolve().parents[2]
if WS.name != 'sentinel_ws':
    WS = WS / 'sentinel_ws'

REFERENCES = {
    'wheels_link', 'lidar_link', 'lidar_aux_link', 'camera_link',
    'camera_optical_frame', 'gun_link', 'muzzle_link',
}
REFERENCE_NAMES = REFERENCES | {name + '_fixed' for name in REFERENCES}

def signature(robot):
    def node(e):
        attrs = dict(e.attrib)
        if e.tag == 'mesh':
            attrs['filename'] = attrs['filename'].split('/meshes/')[-1].replace('sentry_chassis.stl', 'chassis.stl').replace('sentry_gimbal.stl', 'gimbal.stl')
        return (e.tag, sorted(attrs.items()), (e.text or '').strip(), [node(c) for c in e])
    return hashlib.sha256(json.dumps([node(c) for c in sorted(robot, key=lambda e: (e.tag, e.get('name', ''))) if c.tag in ('link', 'joint') and c.get('name') not in REFERENCE_NAMES], sort_keys=True).encode()).hexdigest()

def test_requested_package_boundaries():
    for name in ('rm_arena', 'sentry_description', 'sentry_sim', 'sentry_motion', 'sentry_bringup'):
        assert ET.parse(WS / 'src' / name / 'package.xml').findtext('name') == name
    assert not (WS / 'src/sentry_simulation').exists()
    assert not (WS / 'src/sentry_sim/meshes').exists()
    assert not (WS / 'src/sentry_bringup/src').exists()

def test_preserved_robot_and_gazebo_composition():
    description = ET.fromstring(xacro.process_file(str(WS / 'src/sentry_description/urdf/sentry.urdf.xacro')).toxml())
    simulation = ET.fromstring(xacro.process_file(str(WS / 'src/sentry_sim/urdf/sentry_sim.urdf.xacro')).toxml())
    assert not description.findall('gazebo')
    assert signature(description) == signature(simulation)
    assert len(simulation.findall('.//plugin')) == 2
    assert len(simulation.findall("joint[@type='continuous']")) == 5
    for mesh in description.findall('.//mesh'):
        assert mesh.get('filename').startswith('package://sentry_description/meshes/')
        assert (WS / 'src/sentry_description' / mesh.get('filename').split('sentry_description/')[1]).is_file()


def test_standalone_motion_declares_frontend_dependencies():
    package = ET.parse(WS / 'src/sentry_motion/package.xml').getroot()
    dependencies = {e.text for e in package if e.tag in ('depend', 'exec_depend')}
    assert {'python3-pyqt5', 'rclpy'} <= dependencies


def test_cad_exporter_recreates_the_split_model(tmp_path):
    import importlib.util
    spec = importlib.util.spec_from_file_location('sentry_model_layout', WS / 'tools/sentry_model_layout.py')
    exporter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(exporter)
    robot = ET.fromstring(xacro.process_file(str(WS / 'src/sentry_sim/urdf/sentry_sim.urdf.xacro')).toxml())
    description, simulation = tmp_path / 'description', tmp_path / 'simulation'
    exporter.write_model(robot, description, simulation)
    restored = ET.fromstring(xacro.process_file(str(description / 'urdf/sentry.urdf.xacro')).toxml())
    assert signature(restored) == signature(robot)
    assert len(restored.findall('.//visual/geometry/mesh')) == 0
    assert len(ET.parse(simulation / 'urdf/sentry_sim.urdf.xacro').findall('.//plugin')) == 2
    assert not restored.findall('gazebo')


def test_motion_launch_starts_a_single_keyboard_node(tmp_path, monkeypatch):
    """键盘窗口与看门狗已合并成一个进程：launch 里只剩一个 Node，没有会话前缀。"""
    monkeypatch.setenv('ROS_LOG_DIR', str(tmp_path / 'launch_logs'))
    import importlib.util
    from launch.actions import DeclareLaunchArgument
    spec = importlib.util.spec_from_file_location(
        'motion_launch', WS / 'src/sentry_motion/launch/motion.launch.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    description = module.generate_launch_description()
    names = {a.name for a in description.entities
             if isinstance(a, DeclareLaunchArgument)}
    assert names == {'keyboard', 'linear_speed', 'angular_speed', 'spin_speed'}
    nodes = [e for e in description.entities if type(e).__name__ == 'Node']
    assert len(nodes) == 1
