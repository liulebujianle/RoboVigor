"""Check four independently rotating wheel frames without per-roller TF."""
from collections import Counter
import importlib.util
from pathlib import Path
import math
import subprocess
import xml.etree.ElementTree as ET

import numpy as np
import xacro
import yaml

PACKAGE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'description_launch', PACKAGE / 'launch/description.launch.py')
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def test_display_keeps_all_geometry_on_four_main_wheels():
    """Preserve wheel centers, axes and the whole CAD appearance."""
    physics = xacro.process_file(str(PACKAGE / 'urdf/sentry.urdf.xacro')).toxml()
    raw = ET.fromstring(physics)
    display = ET.fromstring(model.display_description(physics))
    assert len(display.findall('.//visual/geometry/mesh')) == 0
    assert len(raw.findall('.//visual/geometry/mesh')) == 0
    assert Counter(m.get('filename') for m in raw.findall('.//visual/geometry/mesh')) == Counter(
        m.get('filename') for m in display.findall('.//visual/geometry/mesh'))
    assert len(display.findall('.//collision/geometry/cylinder')) == 4
    assert not any(link.get('name').startswith('roller_') for link in display.findall('link'))
    assert display.find("link[@name='wheels_link']") is None
    assert not display.findall('gazebo')
    for i in range(1, 5):
        name = f'wheel_{i}_link'
        link = display.find(f"link[@name='{name}']")
        assert len(link.findall('visual')) == 1
        joint = display.find(f"joint[@name='wheel_{i}_joint']")
        original = raw.find(f"joint[@name='wheel_{i}_joint']")
        assert joint.get('type') == 'continuous'
        assert joint.find('origin').attrib == original.find('origin').attrib
        assert joint.find('axis').attrib == original.find('axis').attrib
    assert len(display.findall("joint[@type='continuous']")) == 5
    assert len(raw.findall("joint[@type='continuous']")) == 5


def test_roller_visual_origin_is_composed_in_parent_wheel():
    """Fold a rotated mount correctly rather than moving a mesh to the origin."""
    description = f'''<robot name="test"><link name="wheel_1_link"/>
<link name="roller_001_link"><visual><origin xyz="1 0 0"/>
<geometry><mesh filename="roller.stl"/></geometry></visual></link>
<joint name="roller_001_joint" type="continuous"><parent link="wheel_1_link"/>
<child link="roller_001_link"/><origin xyz="0 1 0" rpy="0 0 {math.pi / 2}"/>
<axis xyz="1 0 0"/></joint></robot>'''
    output = ET.fromstring(model.display_description(description))
    visual = output.find("link[@name='wheel_1_link']/visual")
    xyz = list(map(float, visual.find('origin').get('xyz').split()))
    assert np.allclose(xyz, [0., 2., 0.])
    assert np.allclose(model.origin(visual.find('origin'))[:3, :3],
                       [[0, -1, 0], [1, 0, 0], [0, 0, 1]], atol=1e-10)
    assert not output.findall('joint')


def test_public_rviz_has_no_bottom_group_or_marker_renderer():
    """Use standard RobotModel and one TF at each actual main axle."""
    assert not (PACKAGE / 'scripts/wheel_visuals.py').exists()
    assert not (PACKAGE / 'scripts/tf_router.py').exists()
    assert not any(name.startswith('wheels_link') for name in yaml.safe_load(
        (PACKAGE / 'config/frames.yaml').read_text())['frames'])
    for path in PACKAGE.parent.glob('*/rviz/*.rviz'):
        config = yaml.safe_load(path.read_text())
        displays = config['Visualization Manager']['Displays']
        assert not any(d.get('Name') in ('Wheel Visuals', 'Wheel Center TF') for d in displays)
        robot = next(d for d in displays if d['Class'] == 'rviz_default_plugins/RobotModel')
        assert robot['Description Topic']['Value'] == '/robot_description'
        assert robot['Alpha'] == 1.
        tf = next(d for d in displays if d['Class'] == 'rviz_default_plugins/TF')
        assert 'wheels_link' not in tf['Frames']
        assert all(tf['Frames'][f'wheel_{i}_link']['Value'] for i in range(1, 5))


def test_physics_publisher_is_executable_on_linux(tmp_path):
    """Exercise the actual shebang before Gazebo waits for a missing publisher."""
    script = PACKAGE / 'scripts/description_publisher.py'
    probe = tmp_path / 'publisher_shebang'
    probe.write_bytes(script.read_bytes().split(b'\n', 1)[0] + b'\npass\n')
    probe.chmod(0o700)
    result = subprocess.run([str(probe)], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stdout + result.stderr


def test_rviz_receives_field_published_before_it_starts():
    """Late RViz instances must request the retained field mesh."""
    for path in PACKAGE.parent.glob('*/rviz/*.rviz'):
        config = yaml.safe_load(path.read_text())
        displays = config['Visualization Manager']['Displays']
        arena = next(d for d in displays if d['Class'] == 'rviz_default_plugins/Marker')
        assert arena['Topic']['Value'] == '/arena_marker'
        assert arena['Topic']['Durability Policy'] == 'Transient Local', str(path)


def test_default_rviz_view_shows_the_field():
    """A close wheel view must not hide the arena on a normal launch."""
    for path in PACKAGE.parent.glob('*/rviz/*.rviz'):
        view = yaml.safe_load(path.read_text())['Visualization Manager']['Views']['Current']
        assert view['Target Frame'] in ('world', '<Fixed Frame>'), str(path)
        assert view['Distance'] >= 16
        assert view['Focal Point']['X'] == 6 and view['Focal Point']['Y'] == 4
