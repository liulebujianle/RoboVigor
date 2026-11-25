"""检查分包结构和车体模型。"""
from pathlib import Path
import xml.etree.ElementTree as ET
import xacro

WS = Path(__file__).resolve().parents[2]


def signature(robot, tags=('link', 'joint')):
    """保留完整的坐标、网格 URI 和动力学参数，只忽略排版和顶层顺序。"""
    return sorted(ET.canonicalize(ET.tostring(node, encoding='unicode'), strip_text=True)
                  for node in robot if node.tag in tags)

def test_requested_package_boundaries():
    for name in ('sentry_map', 'sentry_description', 'sentry_sim', 'sentry_motion', 'sentry_bringup'):
        assert ET.parse(WS / 'src' / name / 'package.xml').findtext('name') == name
    assert not (WS / 'src/sentry_simulation').exists()
    assert not (WS / 'src/sentry_sim/meshes').exists()
    assert (WS / 'src/sentry_bringup/src/sentry_bringup/__init__.py').is_file()

def test_preserved_robot_and_gazebo_composition():
    description = ET.fromstring(xacro.process_file(str(WS / 'src/sentry_description/urdf/sentry.urdf.xacro')).toxml())
    simulation = ET.fromstring(xacro.process_file(str(WS / 'src/sentry_sim/urdf/sentry_sim.urdf.xacro')).toxml())
    assert not description.findall('gazebo')
    assert signature(description) == signature(simulation)
    native = {p.get('filename') for p in simulation.findall('gazebo/plugin')}
    assert native == {'libsentry_gimbal_stabilizer.so', 'libsentry_omni_drive.so'}
    mounts = {g.get('reference'): sensor for g in simulation.findall('gazebo') for sensor in g.findall('sensor')}
    assert len(simulation.findall('.//sensor')) == 2
    assert set(mounts) == {'odin1_lite_link', 'mid360s_link'}
    for frame, sensor in mounts.items():
        assert sensor.get('type') == 'gpu_ray'
        assert sensor.findtext('visualize') == 'true', frame
        assert sensor.findtext('plugin/frame_name') == frame
        assert [float(v) for v in sensor.findtext('pose').split()] == [0.0] * 6
        assert sensor.find('plugin').get('filename') == 'libgazebo_ros_ray_sensor.so'
    assert len(simulation.findall('.//plugin')) == 4
    assert len(simulation.findall("joint[@type='continuous']")) == 6
    for mesh in description.findall('.//mesh'):
        assert mesh.get('filename').startswith('package://sentry_description/meshes/')
        assert (WS / 'src/sentry_description' / mesh.get('filename').split('sentry_description/')[1]).is_file()


def test_standalone_motion_declares_frontend_dependencies():
    package = ET.parse(WS / 'src/sentry_motion/package.xml').getroot()
    dependencies = {e.text for e in package if e.tag in ('depend', 'exec_depend')}
    assert {'python3-pyqt5', 'rclpy'} <= dependencies


def test_cad_exporter_recreates_the_split_model(tmp_path, monkeypatch):
    import importlib.util
    spec = importlib.util.spec_from_file_location('sentry_model_layout', WS / 'tools/sentry_model_layout.py')
    exporter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(exporter)
    robot = ET.fromstring(xacro.process_file(str(WS / 'src/sentry_sim/urdf/sentry_sim.urdf.xacro')).toxml())
    description, simulation = tmp_path / 'description', tmp_path / 'simulation'
    exporter.write_model(robot, description, simulation)
    restored = ET.fromstring(xacro.process_file(str(description / 'urdf/sentry.urdf.xacro')).toxml())
    assert signature(restored) == signature(robot)
    assert len(restored.findall('.//visual/geometry/mesh')) == 8
    assert not restored.findall('gazebo')
    monkeypatch.setattr(xacro.substitution_args, '_eval_find', lambda name: description.as_posix()
                        if name == 'sentry_description' else WS.joinpath('src', name).as_posix())
    restored_sim = ET.fromstring(xacro.process_file(str(simulation / 'urdf/sentry_sim.urdf.xacro')).toxml())
    assert signature(restored_sim, ('link', 'joint', 'gazebo')) == signature(robot, ('link', 'joint', 'gazebo'))


def test_exporter_migrates_legacy_uris_without_rewriting_modern_mesh_names(tmp_path):
    import importlib.util
    spec = importlib.util.spec_from_file_location('sentry_model_layout', WS / 'tools/sentry_model_layout.py')
    exporter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(exporter)
    robot = ET.fromstring('<robot><link name="body"/></robot>')
    uris = ['package://sentry_simulation/meshes/sentry_chassis.stl',
            'package://sentry_simulation/meshes/sentry_gimbal.stl',
            'package://sentry_simulation/meshes/other.stl',
            'package://sentry_description/meshes/sentry_chassis.stl']
    for uri in uris:
        visual = ET.SubElement(robot.find('link'), 'visual')
        ET.SubElement(ET.SubElement(visual, 'geometry'), 'mesh', filename=uri)
    exporter.write_model(robot, tmp_path / 'description', tmp_path / 'sim')
    assert [m.get('filename') for m in robot.findall('.//mesh')] == uris
    exported = ET.parse(tmp_path / 'description/urdf/chassis.xacro')
    assert [m.get('filename') for m in exported.findall('.//mesh')] == [
        'package://sentry_description/meshes/chassis.stl',
        'package://sentry_description/meshes/gimbal.stl',
        'package://sentry_description/meshes/other.stl', uris[-1]]


def test_motion_launch_starts_a_single_keyboard_node(tmp_path, monkeypatch):
    """键盘窗口和看门狗共用一个节点，启动文件只创建一次。"""
    monkeypatch.setenv('ROS_LOG_DIR', str(tmp_path / 'launch_logs'))
    import importlib.util
    from launch.actions import DeclareLaunchArgument
    spec = importlib.util.spec_from_file_location(
        'motion_launch', WS / 'src/sentry_motion/launch/sentry_motion.launch.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    description = module.generate_launch_description()
    names = {a.name for a in description.entities
             if isinstance(a, DeclareLaunchArgument)}
    assert names == {'keyboard', 'linear_speed', 'angular_speed', 'spin_speed'}
    nodes = [e for e in description.entities if type(e).__name__ == 'Node']
    assert len(nodes) == 1
