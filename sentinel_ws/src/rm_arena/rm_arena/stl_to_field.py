#!/usr/bin/env python3
"""将本场地的二进制 STL（毫米、Y 向下）转换为米制 Gazebo 静态模型。"""
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import struct
import xml.etree.ElementTree as ET

RECORD = struct.Struct('<12fH')
COLLADA = 'http://www.collada.org/2005/11/COLLADASchema'
COLORS = {'ground': '0.24 0.43 0.27 1', 'top': '0.65 0.69 0.74 1',
          'side': '0.32 0.36 0.42 1'}
# 本次输入中最后 155 面组成向内的封闭围挡压顶；仅对已核对的文件修正绕序。
RIM_SOURCE_SHA256 = 'aba82019962f672f819cb90c7be33face70faa4cfbf9ec33b44440e84dc68ce9'


def sha256(path):
    """记录输入文件指纹，区分相同文件名的不同模型。"""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normal(triangle):
    """按顶点绕序重算法线；零面积面拒绝导入。"""
    a, b, c = triangle
    u = [b[i] - a[i] for i in range(3)]
    v = [c[i] - a[i] for i in range(3)]
    n = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2],
         u[0] * v[1] - u[1] * v[0])
    length = math.sqrt(sum(value * value for value in n))
    if length <= 1e-12:
        raise ValueError('STL 含零面积三角面')
    return tuple(value / length for value in n)


def read_stl(path):
    """保持既有场地朝向：内场西南角为原点，比赛地面为 z=0。"""
    data = Path(path).read_bytes()
    if len(data) < 84:
        raise ValueError('需要完整的二进制 STL 文件')
    count = struct.unpack_from('<I', data, 80)[0]
    if not count or len(data) != 84 + count * RECORD.size:
        raise ValueError('STL 面数与文件长度不符，或输入不是二进制 STL')
    triangles = []
    for record in RECORD.iter_unpack(data[84:]):
        values = record[3:12]
        if not all(math.isfinite(v) for v in values):
            raise ValueError('STL 顶点包含 NaN 或无穷值')
        # 原始毫米坐标：X/Z 水平，Y 向下，比赛地面 Y=420。
        triangle = tuple((12.3 - values[i] / 1000,
                          8.3 - values[i + 2] / 1000,
                          .42 - values[i + 1] / 1000) for i in (0, 3, 6))
        normal(triangle)
        triangles.append(triangle)
    if hashlib.sha256(data).hexdigest() == RIM_SOURCE_SHA256:
        triangles[-155:] = [(a, c, b) for a, b, c in triangles[-155:]]
    return triangles


def write_dae(path, triangles):
    """生成带明确材质绑定的 DAE；不依赖旧贴图或 CAD 软件。"""
    ET.register_namespace('', COLLADA)

    def node(parent, tag, text=None, **attrs):
        child = ET.SubElement(parent, f'{{{COLLADA}}}{tag}', attrs)
        if text is not None:
            child.text = str(text)
        return child

    root = ET.Element(f'{{{COLLADA}}}COLLADA', version='1.4.1')
    asset = node(root, 'asset')
    node(asset, 'created', '2026-11-02T00:00:00Z')
    node(asset, 'modified', '2026-11-02T00:00:00Z')
    node(asset, 'unit', name='meter', meter='1')
    node(asset, 'up_axis', 'Z_UP')
    effects, materials = node(root, 'library_effects'), node(root, 'library_materials')
    for name, color in COLORS.items():
        effect = node(effects, 'effect', id=f'{name}-effect')
        profile = node(effect, 'profile_COMMON')
        lambert = node(node(profile, 'technique', sid='common'), 'lambert')
        node(node(lambert, 'diffuse'), 'color', color)
        material = node(materials, 'material', id=f'{name}-material', name=name)
        node(material, 'instance_effect', url=f'#{name}-effect')

    mesh = node(node(node(root, 'library_geometries'), 'geometry',
                     id='field-geometry', name='field'), 'mesh')
    positions = [value for tri in triangles for vertex in tri for value in vertex]
    normals = [value for tri in triangles for _ in range(3) for value in normal(tri)]
    for name, values in (('positions', positions), ('normals', normals)):
        source = node(mesh, 'source', id=name)
        node(source, 'float_array', ' '.join(f'{v:.9g}' for v in values),
             id=f'{name}-array', count=str(len(values)))
        accessor = node(node(source, 'technique_common'), 'accessor',
                        source=f'#{name}-array', count=str(len(values) // 3), stride='3')
        for axis in 'XYZ':
            node(accessor, 'param', name=axis, type='float')
    node(node(mesh, 'vertices', id='field-vertices'), 'input',
         semantic='POSITION', source='#positions')
    groups = defaultdict(list)
    for i, triangle in enumerate(triangles):
        nz = normal(triangle)[2]
        material = ('ground' if nz > .9 and max(abs(p[2]) for p in triangle) < 1e-5
                    else 'top' if nz > .9 else 'side')
        groups[material].extend(range(i * 3, i * 3 + 3))
    for material, indices in groups.items():
        faces = node(mesh, 'triangles', material=material, count=str(len(indices) // 3))
        node(faces, 'input', semantic='VERTEX', source='#field-vertices', offset='0')
        # Gazebo Classic 按输入数量读取索引步长，显式使用两个交错索引。
        node(faces, 'input', semantic='NORMAL', source='#normals', offset='1')
        node(faces, 'p', ' '.join(f'{i} {i}' for i in indices))
    scene = node(node(root, 'library_visual_scenes'), 'visual_scene', id='field-scene')
    instance = node(node(scene, 'node', id='field-node'), 'instance_geometry', url='#field-geometry')
    bindings = node(node(instance, 'bind_material'), 'technique_common')
    for material in groups:
        node(bindings, 'instance_material', symbol=material, target=f'#{material}-material')
    node(node(root, 'scene'), 'instance_visual_scene', url='#field-scene')
    ET.indent(root)
    ET.ElementTree(root).write(path, encoding='utf-8', xml_declaration=True)


def convert(source, out):
    """外观与碰撞来自相同三角面，场地静止且保留原始表面。"""
    source, out = Path(source), Path(out)
    source_data = source.read_bytes()
    triangles = read_stl(source)
    meshes = out / 'meshes'
    meshes.mkdir(parents=True, exist_ok=True)
    (out / 'source').mkdir(exist_ok=True)
    (out / 'source/rmul_2027.stl').write_bytes(source_data)
    write_dae(meshes / 'field.dae', triangles)
    with (meshes / 'field_collision.stl').open('wb') as stream:
        stream.write(b'RoboVigor normalized static field'.ljust(80, b'\0'))
        stream.write(struct.pack('<I', len(triangles)))
        for triangle in triangles:
            stream.write(RECORD.pack(*normal(triangle),
                                    *(v for p in triangle for v in p), 0))
    root = ET.Element('sdf', version='1.6')
    model = ET.SubElement(root, 'model', name='rmul_2027')
    ET.SubElement(model, 'static').text = 'true'
    link = ET.SubElement(model, 'link', name='arena')
    for kind, filename in (('visual', 'field.dae'), ('collision', 'field_collision.stl')):
        item = ET.SubElement(link, kind, name=f'field_{kind}')
        mesh = ET.SubElement(ET.SubElement(item, 'geometry'), 'mesh')
        ET.SubElement(mesh, 'uri').text = f'model://rmul_2027/meshes/{filename}'
        if kind == 'collision':
            ode = ET.SubElement(ET.SubElement(ET.SubElement(item, 'surface'), 'friction'), 'ode')
            for tag in ('mu', 'mu2'):
                ET.SubElement(ode, tag).text = '0.9'
    ET.indent(root)
    ET.ElementTree(root).write(out / 'model.sdf', encoding='utf-8', xml_declaration=True)
    (out / 'model.config').write_text('''<?xml version="1.0"?>
<model>
  <name>RMUL 2027 3v3 (STL)</name><version>3.0</version>
  <sdf version="1.6">model.sdf</sdf>
  <author><name>RoboVigor STL import</name></author>
  <description>User STL; metres, Z up; same geometry for visual and static collision.</description>
</model>
''', encoding='utf-8')
    vertices = [p for triangle in triangles for p in triangle]
    stats = {
        'source': source.name, 'source_sha256': sha256(source), 'triangles': len(triangles),
        'units': 'metres', 'up_axis': 'Z', 'play_surface_z': 0.0,
        'transform': 'x=12.3-X/1000; y=8.3-Z/1000; z=0.42-Y/1000',
        'extent': {axis: [round(min(p[i] for p in vertices), 6),
                          round(max(p[i] for p in vertices), 6)]
                   for i, axis in enumerate('xyz')},
        'collision': 'static triangle mesh; original STL topology preserved',
        'colors': 'generated flat colors; STL contains no textures',
        'reversed_rim_faces': 155 if sha256(source) == RIM_SOURCE_SHA256 else 0,
    }
    (meshes / 'field_stats.json').write_text(
        json.dumps(stats, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return stats


def main(argv=None):
    """显式生成资源；启动仿真不会再次转换或覆盖模型。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stl', required=True, help='本场地原始二进制 STL，单位毫米')
    parser.add_argument('--out', required=True, help='输出 rmul_2027 模型目录')
    args = parser.parse_args(argv)
    try:
        stats = convert(args.stl, args.out)
    except (OSError, ValueError) as error:
        parser.exit(1, f'STL 场地生成失败：{error}\n')
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
