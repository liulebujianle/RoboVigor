"""检查显示模型的四个独立轮轴及滚子合并。"""
import importlib.util
from pathlib import Path
import math
import xml.etree.ElementTree as ET

import numpy as np
import xacro
import yaml

PACKAGE = Path(__file__).resolve().parents[1]
DESCRIPTION_RVIZ = PACKAGE / 'rviz/sentry_description.rviz'
BRINGUP_RVIZ = PACKAGE.parent / 'sentry_bringup/rviz/sentry_navigation.rviz'
MAP_RVIZ = PACKAGE.parent / 'sentry_map/rviz/sentry_map.rviz'
spec = importlib.util.spec_from_file_location(
    'display_description', PACKAGE / 'src/sentry_description/sentry_display_description.py')
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def test_display_keeps_all_geometry_on_four_main_wheels():
    """检查显示转换保留轮心、轮轴和几何外形。"""
    physics = xacro.process_file(str(PACKAGE / 'urdf/sentry.urdf.xacro')).toxml()
    raw = ET.fromstring(physics)
    display = ET.fromstring(model.display_description(physics))
    def meshes(robot):
        return sorted((link.get('name'), mesh.get('filename')) for link in robot.findall('link')
                      for mesh in link.findall('visual/geometry/mesh'))

    assert len(meshes(raw)) == 8
    assert meshes(display) == meshes(raw)
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
    for robot in (raw, display):
        assert len(robot.findall("joint[@type='continuous']")) == 6
        small = robot.find("joint[@name='small_yaw_joint']")
        assert small.find('parent').get('link') == 'gimbal_yaw_link'
        assert small.find('child').get('link') == 'small_yaw_link'
    for frame in ('mid360s_link', 'odin1_lite_mount_link'):
        assert display.find(f"link[@name='{frame}']/visual") is not None
    assert len([j for j in display.findall('joint') if j.get('type') != 'fixed']) == 6


def test_small_yaw_indicator_is_only_on_the_gui_display():
    physics = xacro.process_file(str(PACKAGE / 'urdf/sentry.urdf.xacro')).toxml()
    query = "link[@name='small_yaw_link']/visual[@name='small_yaw_indicator']"
    assert ET.fromstring(physics).find(query) is None
    assert ET.fromstring(model.display_description(physics)).find(query) is None
    gui = ET.fromstring(model.display_description(physics, show_small_yaw_marker=True))
    marker = gui.find(query)
    assert marker is not None and marker.find('geometry/sphere') is not None
    offset = model.origin(marker.find('origin'))[:2, 3]
    assert np.linalg.norm(offset) > 0


def test_roller_visual_origin_is_composed_in_parent_wheel():
    """检查滚子安装变换与几何原点正确复合。"""
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
    """检查 RViz 使用标准 RobotModel，并显示各主轮轴的 TF。"""
    assert not (PACKAGE / 'scripts/wheel_visuals.py').exists()
    assert not (PACKAGE / 'scripts/tf_router.py').exists()
    for path in (DESCRIPTION_RVIZ, BRINGUP_RVIZ, MAP_RVIZ):
        config = yaml.safe_load(path.read_text(encoding='utf-8'))
        displays = config['Visualization Manager']['Displays']
        assert not any(d.get('Name') in ('Wheel Visuals', 'Wheel Center TF') for d in displays)
        robot = next(d for d in displays if d['Class'] == 'rviz_default_plugins/RobotModel')
        assert robot['Description Topic']['Value'] == '/robot_description'
        assert robot['Alpha'] == 1.
        tf = next(d for d in displays if d['Class'] == 'rviz_default_plugins/TF')
        assert 'wheels_link' not in tf['Frames']
        assert 'front_camera_mesh_frame' not in tf['Frames']
        assert tf['Enabled'] and tf['Value'] and tf['Show Axes'], path
        for name in ('base_link', 'gimbal_yaw_link', 'small_yaw_link',
                     'mid360s_link', 'odin1_lite_link',
                     'barrel_mesh_frame', 'navigation_camera_optical_frame',
                     *(f'wheel_{i}_link' for i in range(1, 5))):
            assert tf['Frames'][name]['Value'] is True, (path, name)
        for name in ('odin1_lite_mount_link', 'lidar_link',
                     'front_camera_link', 'front_camera_optical_frame'):
            assert tf['Frames'][name]['Value'] is False, (path, name)
        if path != MAP_RVIZ:
            assert [p['Class'] for p in config['Panels']] == ['rviz_common/Displays']
            assert config['Visualization Manager']['Tools'] == [
                {'Class': 'rviz_default_plugins/MoveCamera'}]
            types = [d['Class'].rsplit('/', 1)[-1] for d in displays]
            expected = ['RobotModel', 'Marker', 'TF']
            if path == BRINGUP_RVIZ:
                expected.extend(['PointCloud2', 'PointCloud2'])
                topics = {d['Topic']['Value'] for d in displays if
                          d['Class'] == 'rviz_default_plugins/PointCloud2' and d['Enabled']}
                assert topics == {'/lidar/points', '/mid360s/points'}
            else:
                expected.append('MarkerArray')
            assert sorted(types) == sorted(expected)


def test_camera_detail_draws_both_local_frames():
    path = PACKAGE / 'rviz/sentry_front_camera.rviz'
    manager = yaml.safe_load(path.read_text(encoding='utf-8'))['Visualization Manager']
    assert manager['Global Options']['Fixed Frame'] == 'front_camera_link'
    axes = {d['Reference Frame']: d['Length'] for d in manager['Displays']
            if d['Class'] == 'rviz_default_plugins/Axes' and d['Enabled'] and d['Value']}
    assert 0 < axes['front_camera_link'] < axes['front_camera_optical_frame']


def test_display_keeps_barrel_reference_without_front_camera_marker():
    physics = xacro.process_file(str(PACKAGE / 'urdf/sentry.urdf.xacro')).toxml()
    raw = ET.fromstring(physics)
    upper = raw.find("link[@name='gimbal_yaw_link']/visual")
    # 移动网格后，保留的外观参考系也必须跟着它移动。
    if upper.find('origin') is not None:
        upper.remove(upper.find('origin'))
    ET.SubElement(upper, 'origin', xyz='0.4 0.3 0.2', rpy='0.2 0 0')
    display = ET.fromstring(model.display_description(ET.tostring(raw, encoding='unicode')))
    assert display.find("link[@name='front_camera_mesh_frame']") is None
    assert display.find("joint/child[@link='front_camera_mesh_frame']") is None
    assert display.find("link[@name='navigation_camera_optical_frame']") is not None
    assert raw.find("link[@name='barrel_mesh_frame']") is None
    joint = display.find("joint[@name='barrel_mesh_frame_fixed']")
    assert joint.get('type') == 'fixed'
    assert joint.find('parent').get('link') == 'gimbal_yaw_link'
    assert joint.find('child').get('link') == 'barrel_mesh_frame'
    in_mesh = np.linalg.solve(model.origin(upper.find('origin')), model.origin(joint.find('origin')))
    np.testing.assert_allclose(in_mesh, np.eye(4), atol=1e-10)


def test_rviz_receives_field_published_before_it_starts():
    """检查 RViz 使用 Transient Local 接收先前发布的场地 Marker。"""
    for path in (DESCRIPTION_RVIZ, BRINGUP_RVIZ, MAP_RVIZ):
        config = yaml.safe_load(path.read_text(encoding='utf-8'))
        displays = config['Visualization Manager']['Displays']
        arena = next(d for d in displays if d['Class'] == 'rviz_default_plugins/Marker')
        assert arena['Topic']['Value'] == '/arena_marker'
        assert arena['Topic']['Durability Policy'] == 'Transient Local', str(path)


def test_map_overview_frames_the_whole_field():
    """检查场地预览视角覆盖整个场地。"""
    view = yaml.safe_load(MAP_RVIZ.read_text())['Visualization Manager']['Views']['Current']
    assert view['Target Frame'] in ('world', '<Fixed Frame>')
    assert view['Distance'] >= 16
    assert view['Focal Point'] == {'X': 6, 'Y': 4, 'Z': 0}


def test_robot_views_follow_the_vehicle():
    """机器人视图以实际车体为中心，独立预览比场内驾驶更近。"""
    for path, distance in ((DESCRIPTION_RVIZ, 1.8), (BRINGUP_RVIZ, 3.8)):
        view = yaml.safe_load(path.read_text(encoding='utf-8'))['Visualization Manager']['Views']['Current']
        assert view['Target Frame'] == 'base_link'
        assert view['Distance'] == distance
        assert view['Focal Point'] == {'X': 0, 'Y': 0, 'Z': 0.2}
