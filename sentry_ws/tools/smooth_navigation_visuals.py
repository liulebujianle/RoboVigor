"""根据原总装重建上装外形、简化底盘、四个全向轮和两台导航雷达的显示网格。

在 sentry_ws 下运行：
  python3 tools/smooth_navigation_visuals.py /path/to/哨兵总装.SLDASM

只在重建显示网格时需要 NumPy 和 SciPy。仿真直接加载包内的 DAE。
"""
import argparse
import math
from pathlib import Path
import struct
import xml.etree.ElementTree as ET

import numpy as np


SENSOR_COLOR = (0.16, 0.18, 0.20)


def read_stl(path):
    data = path.read_bytes()
    count = struct.unpack_from('<I', data, 80)[0]
    record = np.dtype([('normal', '<f4', 3), ('points', '<f4', (3, 3)), ('attr', '<u2')])
    if len(data) != 84 + count * record.itemsize:
        raise ValueError(f'STL 数据长度异常: {path}')
    return np.frombuffer(data, dtype=record, offset=84)['points']


def component_labels(count, pairs):
    """连接 pairs 中的编号，返回每个编号所属部分的标记。"""
    labels = np.arange(count)
    left, right = pairs.T
    while True:
        prev = labels.copy()
        low = np.minimum(labels[left], labels[right])
        np.minimum.at(labels, left, low)
        np.minimum.at(labels, right, low)
        labels = labels[labels]
        if np.array_equal(prev, labels):
            return labels


def split_creases(vertices, faces, angle=38):
    """平滑同一曲面；锐边、薄板背面和不相连的面分别保留法线。"""
    points = vertices[faces]
    normals = np.cross(points[:, 1] - points[:, 0], points[:, 2] - points[:, 0])
    normals /= np.linalg.norm(normals, axis=1)[:, None]

    # 用顶点编号匹配边，保存边两个端点各自对应的面角编号。
    corners = np.arange(faces.size).reshape(-1, 3)
    ends = np.column_stack((corners.ravel(), np.roll(corners, -1, axis=1).ravel()))
    ids = faces.ravel()[ends]
    reverse = ids[:, 0] > ids[:, 1]
    ids[reverse] = ids[reverse, ::-1]
    ends[reverse] = ends[reverse, ::-1]
    order = np.lexsort((ids[:, 1], ids[:, 0]))
    ids, ends = ids[order], ends[order]
    starts = np.flatnonzero(np.r_[True, np.any(np.diff(ids, axis=0), axis=1)])
    first = starts[np.diff(np.r_[starts, len(ids)]) == 2]
    a, b = ends[first], ends[first + 1]
    cosine = (normals[a[:, 0] // 3] * normals[b[:, 0] // 3]).sum(axis=1)
    smooth = cosine >= math.cos(math.radians(angle))
    labels = component_labels(faces.size, np.column_stack((a[smooth].ravel(), b[smooth].ravel())))
    roots, indices = np.unique(labels, return_inverse=True)
    vertices = vertices[faces.ravel()[roots]]
    faces = indices.reshape(-1, 3)
    return vertices, faces, unit_normals(vertices, faces)


def odin_surface(stl):
    """同一小格内的顶点取平均，减去设备外壳上的细碎三角面。"""
    vertices, indices = np.unique(stl.reshape(-1, 3), axis=0, return_inverse=True)
    coords = vertices.astype(float) * 1000
    cell_mm = 1.8
    cells = np.rint(coords / cell_mm).astype(np.int32)
    _, cluster = np.unique(cells, axis=0, return_inverse=True)
    cluster = cluster.ravel()
    vertices = np.column_stack([np.bincount(cluster, weights=v) for v in coords.T])
    vertices /= np.bincount(cluster)[:, None]
    faces = cluster[indices.reshape(-1, 3)]
    a, b, c = vertices[faces].transpose(1, 0, 2)
    faces = faces[np.linalg.norm(np.cross(b-a, c-a), axis=1) > 1e-6]
    _, keep = np.unique(np.sort(faces, axis=1), axis=0, return_index=True)
    faces = faces[np.sort(keep)]
    return split_creases(vertices / 1000, faces)


def unit_normals(vertices, faces):
    """相邻面按顶角加权，保留平面并让轮缘、圆角连续着色。"""
    a, b, c = vertices[faces].transpose(1, 0, 2)
    areas = np.cross(b-a, c-a)
    areas /= np.maximum(np.linalg.norm(areas, axis=1), 1e-20)[:, None]
    normals = np.zeros_like(vertices)
    for i in range(3):
        center = vertices[faces[:, i]]
        p = vertices[faces[:, (i+1)%3]] - center
        q = vertices[faces[:, (i+2)%3]] - center
        angles = np.arctan2(np.linalg.norm(np.cross(p,q),axis=1), (p*q).sum(axis=1))
        np.add.at(normals, faces[:, i], angles[:, None] * areas)
    lengths = np.linalg.norm(normals, axis=1)
    if np.any(lengths < 1e-12):
        raise ValueError('显示网格含无法确定法线的顶点')
    return normals / lengths[:, None]


def mid_housing():
    """65×65×60 mm 的简化外壳。圆角底座和光滑扫描罩共用环形截面。"""
    # 高度、半宽（毫米）、超椭圆指数：2 为圆，较大的数给底座保留四个圆角。
    profile = [
        (-30, 29, 6), (-29.8, 30.8, 6), (-29.2, 31.8, 6), (-28, 32.5, 6),
        (-8, 32.5, 6), (-6, 32, 6), (-4, 30, 4), (-3, 29.6, 2),
        (8, 29.6, 2), (17, 28.5, 2), (23, 26.4, 2), (27, 23.5, 2),
        (29, 20, 2), (29.8, 16.5, 2), (30, 14, 2),
    ]
    segments = 96
    angles = np.arange(segments) * (2 * math.pi / segments)
    x, y = np.cos(angles), np.sin(angles)
    rings = []
    for z, half_width, power in profile:
        radius = half_width / (abs(x)**power + abs(y)**power)**(1/power)
        rings.append(np.column_stack((radius*x, radius*y, np.full(segments, z))))
    vertices = np.vstack([*rings, [0, 0, -30], [0, 0, 30]]) / 1000
    faces = []
    for row in range(len(rings)-1):
        for i in range(segments):
            a = row*segments+i
            b = row*segments+(i+1) % segments
            faces.extend([(a, b, b+segments), (a, b+segments, a+segments)])
    top = (len(rings)-1)*segments
    for i in range(segments):
        j = (i+1) % segments
        faces.extend([(len(vertices)-2, j, i), (len(vertices)-1, top+i, top+j)])
    faces = np.asarray(faces)
    return vertices, faces, unit_normals(vertices, faces)


def save_dae(path, vertices, faces, normals, rgb):
    """Collada 使用米、Z 向上，每个顶点携带共享法线。"""
    # 共享坐标和法线分别编号，平板的两侧可复用坐标并保留各自的光照。
    vertices, position_id = np.unique(np.round(vertices, 8), axis=0, return_inverse=True)
    normals, normal_id = np.unique(np.round(normals, 6), axis=0, return_inverse=True)
    position_face = position_id.ravel()[faces]
    points = vertices[position_face]
    areas = np.cross(points[:, 1] - points[:, 0], points[:, 2] - points[:, 0])
    keep = np.linalg.norm(areas, axis=1) > 1e-11
    normals /= np.linalg.norm(normals, axis=1)[:, None]
    indices = np.stack((position_face[keep], normal_id.ravel()[faces[keep]]), axis=2)

    def node(parent, tag, **attrs):
        return ET.SubElement(parent, tag, {k: str(v) for k, v in attrs.items()})

    root = ET.Element('COLLADA', xmlns='http://www.collada.org/2005/11/COLLADASchema', version='1.4.1')
    asset = node(root, 'asset')
    for tag in ('created', 'modified'):
        node(asset, tag).text = '2026-11-24T00:00:00Z'
    node(asset, 'unit', name='meter', meter=1)
    node(asset, 'up_axis').text = 'Z_UP'
    effect = node(node(root, 'library_effects'), 'effect', id='paint-fx')
    technique = node(node(effect, 'profile_COMMON'), 'technique', sid='common')
    diffuse = node(node(technique, 'lambert'), 'diffuse')
    node(diffuse, 'color').text = ' '.join(str(v) for v in (*rgb, 1))
    paint = node(node(root, 'library_materials'), 'material', id='paint')
    node(paint, 'instance_effect', url='#paint-fx')
    mesh = node(node(node(root, 'library_geometries'), 'geometry', id='body'), 'mesh')
    for name, values in [('position', vertices), ('normal', normals)]:
        source = node(mesh, 'source', id=name)
        node(source, 'float_array', id=name+'-array', count=values.size).text = ' '.join(
            f'{v:.8g}' for v in values.ravel())
        accessor = node(node(source, 'technique_common'), 'accessor',
                        source='#'+name+'-array', count=len(values), stride=3)
        for axis in 'XYZ':
            node(accessor, 'param', name=axis, type='float')
    verts = node(mesh, 'vertices', id='vertices')
    node(verts, 'input', semantic='POSITION', source='#position')
    tris = node(mesh, 'triangles', count=len(indices), material='paint')
    node(tris, 'input', semantic='VERTEX', source='#vertices', offset=0)
    # Gazebo Classic 按语义个数读取索引，坐标和法线分别占一个位置。
    node(tris, 'input', semantic='NORMAL', source='#normal', offset=1)
    node(tris, 'p').text = ' '.join(map(str, indices.ravel()))
    scene = node(node(root, 'library_visual_scenes'), 'visual_scene', id='scene')
    instance = node(node(scene, 'node', id='model'), 'instance_geometry', url='#body')
    binding = node(node(instance, 'bind_material'), 'technique_common')
    node(binding, 'instance_material', symbol='paint', target='#paint')
    node(node(root, 'scene'), 'instance_visual_scene', url='#scene')
    ET.indent(root, space='  ')
    ET.ElementTree(root).write(path, encoding='utf-8', xml_declaration=True)


def upper_shell(assembly):
    """按每个 CAD 零件单独取外壳，略去紧固件及狭小附件。"""
    from scipy.spatial import ConvexHull, QhullError
    from import_navigation_visuals import iter_component_meshes

    vertices, faces = [], []
    offset = 0
    for group, points, source_faces in iter_component_meshes(assembly):
        if group != 'sentry_turntable':
            continue
        # CAD 缓存还可能保存未被三角面引用的草图点。分开不相连的实体，
        # 避免给相距较远的板件或支架中间架出虚假的外壳。
        points, labels = np.unique(points[source_faces].reshape(-1, 3).round(3),
                                   axis=0, return_inverse=True)
        source_faces = labels.reshape(-1, 3)
        edges = np.column_stack((source_faces.ravel(), np.roll(source_faces, -1, axis=1).ravel()))
        labels = component_labels(len(points), edges)[source_faces[:, 0]]
        for label in np.unique(labels):
            used, indices = np.unique(source_faces[labels == label], return_inverse=True)
            part = points[used]
            if len(part) < 4:
                continue
            centered = part - part.mean(axis=0)
            _, axes = np.linalg.eigh(np.cov(centered.T))
            widths = np.sort(np.ptp(centered @ axes, axis=0))
            if widths[-1] < 24 or widths[-2] < 7:
                continue
            try:
                hull = ConvexHull(part)
            except QhullError:
                continue
            original = indices.reshape(-1, 3)
            a, b, c = centered[original].transpose(1, 0, 2)
            volume = abs(np.einsum('ij,ij->', a, np.cross(b, c))) / 6
            if widths[-1] > 64 and volume < hull.volume * 0.68:
                # 对桁架及带大孔的板件保留原始表面，只合并相邻的细小面。
                cells = np.rint(part / 1.25).astype(np.int32)
                _, cluster = np.unique(cells, axis=0, return_inverse=True)
                cluster = cluster.ravel()
                count = np.bincount(cluster)[:, None]
                part = np.column_stack([np.bincount(cluster, weights=v) for v in part.T]) / count
                triangles = cluster[original]
            else:
                triangles = hull.simplices.copy()
                a, b, c = part[triangles].transpose(1, 0, 2)
                inward = (np.cross(b-a, c-a) * hull.equations[:, :3]).sum(axis=1) < 0
                triangles[inward] = triangles[inward, ::-1]
            a, b, c = part[triangles].transpose(1, 0, 2)
            triangles = triangles[np.linalg.norm(np.cross(b-a, c-a), axis=1) > 1e-5]
            if not len(triangles):
                continue
            _, keep = np.unique(np.sort(triangles, axis=1), axis=0, return_index=True)
            used, indices = np.unique(triangles[np.sort(keep)], return_inverse=True)
            vertices.append(part[used] / 1000)
            faces.append(indices.reshape(-1, 3) + offset)
            offset += len(used)
    if not faces:
        raise ValueError('总装没有可显示的上装外壳')
    return split_creases(np.concatenate(vertices), np.concatenate(faces), angle=40)


def main():
    from parametric_base import write_base

    meshes = Path(__file__).resolve().parents[1] / 'src' / 'sentry_description' / 'meshes'
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('assembly', type=Path, help='原总装 SLDASM，旁边保留配套零件')
    parser.add_argument('--source', type=Path, default=meshes, help='包含 Odin 原始 STL 的目录')
    parser.add_argument('--output', type=Path, default=meshes/'navigation')
    args = parser.parse_args()
    args.output.mkdir(exist_ok=True, parents=True)
    upper = upper_shell(args.assembly)
    save_dae(args.output/'sentry_turntable.dae', *upper, (0.55, 0.58, 0.62))
    write_base(args.output)
    odin = read_stl(args.source/'sentry_odin1_lite.stl')
    save_dae(args.output/'sentry_odin1_lite.dae', *odin_surface(odin), SENSOR_COLOR)
    save_dae(args.output/'sentry_mid360s.dae', *mid_housing(), SENSOR_COLOR)


if __name__ == '__main__':
    main()
