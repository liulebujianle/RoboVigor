"""场地模型自检：范围、地面高度、围挡、平台高度、碰撞盒清单。"""

from pathlib import Path
import json
import xml.etree.ElementTree as ET

import pytest

PACKAGE = Path(__file__).resolve().parents[1]
MODEL = PACKAGE / 'models' / 'rmul_2027'
SDF = MODEL / 'model.sdf'
DAE = MODEL / 'meshes' / 'field.dae'
TEXTURE = MODEL / 'materials' / 'textures' / 'official_top.png'
FIELD = (12.6, 8.6)          # 外轮廓，内场 12 × 8 + 每边 0.3 围挡
WALL_H = 0.42


@pytest.fixture(scope='module')
def items():
    """(size, pose) of every collision box in the generated model."""
    model = ET.parse(SDF).getroot().find('model')
    out = []
    for collision in model.iter('collision'):
        size = [float(v) for v in collision.find('geometry/box/size').text.split()]
        pose = [float(v) for v in collision.find('pose').text.split()]
        out.append((size, pose))
    return out


def test_field_is_static_and_uses_one_mesh():
    """场地必须是 static，视觉只引用一个 DAE。"""
    model = ET.parse(SDF).getroot().find('model')
    assert model.find('static').text == 'true'
    assert [e.text for e in model.iter('uri')] == ['model://rmul_2027/meshes/field.dae']
    assert DAE.is_file()


def test_dae_texture_path_survives_install():
    """DAE 用相对路径引贴图，安装到 share 后仍能解析。"""
    assert TEXTURE.is_file()
    text = DAE.read_text(encoding='utf-8', errors='ignore')
    assert '../materials/textures/official_top.png' in text
    assert '<up_axis>Z_UP</up_axis>' in text
    assert '<unit name="meter" meter="1"/>' in text


def test_floor_plane_is_the_play_surface(items):
    """地台 12.6 × 8.6，顶面正好在 z = 0，车能站在比赛地面上。"""
    size, pose = min(items, key=lambda b: b[1][2])
    assert size[0] == pytest.approx(FIELD[0], abs=1e-3)
    assert size[1] == pytest.approx(FIELD[1], abs=1e-3)
    assert pose[2] + size[2] / 2 == pytest.approx(0.0, abs=1e-3)


def test_walls_close_all_four_sides(items):
    """四条围挡都在 0.42 m，且贴住内场边界（0 / 12 / 0 / 8）。"""
    walls = [(s, p) for s, p in items if abs(s[2] - WALL_H) < 1e-6]
    assert len(walls) >= 4
    edges = {
        'south': any(p[1] - s[1] / 2 <= -0.3 + 1e-3 for s, p in walls),
        'north': any(p[1] + s[1] / 2 >= 8.3 - 1e-3 for s, p in walls),
        'west': any(p[0] - s[0] / 2 <= -0.3 + 1e-3 for s, p in walls),
        'east': any(p[0] + s[0] / 2 >= 12.3 - 1e-3 for s, p in walls),
    }
    assert all(edges.values()), edges
    for _, pose in walls:
        assert pose[2] == pytest.approx(WALL_H / 2, abs=1e-3)


def test_platform_heights_come_from_the_step(items):
    """场内凸起只能是 0.20 / 0.27 / 0.40 m 三档（按 STEP 实测）。"""
    heights = {round(p[2] + s[2] / 2, 2) for s, p in items}
    assert heights <= {0.0, 0.2, 0.27, 0.4, WALL_H}, heights
    assert {0.2, 0.4} <= heights, '高地与平台没有被建出碰撞'


def test_collision_stays_inside_the_outer_footprint(items):
    """所有碰撞盒都不许超出 -0.3…12.3 / -0.3…8.3。"""
    for size, pose in items:
        assert pose[0] - size[0] / 2 >= -0.301
        assert pose[0] + size[0] / 2 <= 12.301
        assert pose[1] - size[1] / 2 >= -0.301
        assert pose[1] + size[1] / 2 <= 8.301


def test_stats_file_matches_the_generated_sdf(items):
    """field_stats.json 是生成器产物，留作可追溯证据。"""
    stats = json.loads((MODEL / 'meshes/field_stats.json').read_text())
    assert stats['triangles'] > 3000
    assert stats['extent']['x'] == [0.0, 12.6]
    assert stats['extent']['y'] == [0.0, 8.6]
    assert len(stats['collision_boxes']) == len(items)
