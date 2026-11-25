"""从哨兵的 SolidWorks 总装缓存导出车体、车轮与 Odin 导航仿真显示网格。

用法：python3 tools/import_navigation_visuals.py /path/to/哨兵总装.SLDASM
所有 STL 以米为单位。碰撞体、惯量和传感器由 URDF 单独定义。
"""
import argparse
from collections import defaultdict
from hashlib import sha256
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import xml.etree.ElementTree as ET

import numpy as np

from import_sentry_cad import write_stl

sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))
from sldprt.assembly import _component_meshes, instance_path, read_directory, rigid_transform
from sldprt.blocks import find_block, read_blocks
from sldprt.savedmesh import read_saved_mesh


# 零位尺寸取自本版总装。换版时可输出到临时目录核对轮心和支架。
ASSEMBLY_SHA256 = '1603d816044d90acff0f7161d34754f31e6c60ac55f6957dcdbc276485d43f4e'
CAD_TO_ROS = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]])
ORIGINS = {
    'sentry_chassis': (0, 0, 0),
    'sentry_turntable': (0, 0, 0.051),
    'sentry_wheel_1': (-0.16731710, 0.16731710, -0.03618833),
    'sentry_wheel_2': (0.16731710, 0.16731710, -0.03618833),
    'sentry_wheel_3': (0.16731710, -0.16731710, -0.03618833),
    'sentry_wheel_4': (-0.16731710, -0.16731710, -0.03618833),
    'sentry_odin1_lite': (0, 0, 0),
}
SENSOR_PARTS = {'O1-Lite-V1.1', 'mid-360-asm（带范围）V2.001'}


def visual_group(path):
    if not path[0].startswith('底盘总装-'):
        return 'sentry_turntable'
    if any('全向轮装配-' in step for step in path):
        wheel_number = path[1].removeprefix('轮组-')
        return 'sentry_wheel_' + wheel_number
    return 'sentry_chassis'


def active_instances(blocks):
    tree = find_block(blocks, 'swXmlContents/COMPINSTANCETREE')
    root = ET.fromstring(tree.inflate())
    for node in root.iter():
        node.tag = node.tag.rsplit('}', 1)[-1]
    models = {model.get('id'): model for model in root.find('swModelList')}
    configs = list(root.find('swConfigurationList'))
    active = next((c for c in configs if c.get('swMostRecentConfiguration') == 'YES'), configs[0])
    skipped_sensors = []

    def walk(model, parent, path):
        for ref in model.findall('swReference'):
            if ref.get('swHidden') == 'YES' or ref.get('swSuppressed') == 'YES':
                continue
            name = ref.get('swName')
            steps = path + [f"{name}-{ref.get('swReferenceNumber')}"]
            if name in SENSOR_PARTS:
                skipped_sensors.append(name)
                if name == 'O1-Lite-V1.1':
                    # 独立网格保留设备 CAD 原点，机体 +Z 前、+X 左、+Y 上。
                    local = np.eye(4)
                    local[:3, :3] = CAD_TO_ROS.T @ np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]])
                    yield '/'.join(steps), 'sentry_odin1_lite', local
                continue
            matrix = np.array(rigid_transform(ref.get('swTransform'))[0]).reshape(4, 4).T
            transform = parent @ matrix
            child = models[ref.get('swModelRef')]
            if child.find('swReference') is not None:
                yield from walk(child, transform, steps)
            else:
                yield '/'.join(steps), visual_group(steps), transform

    yield from walk(models[active.get('swModelRef')], np.eye(4), [])
    if sorted(skipped_sensors) != sorted(SENSOR_PARTS):
        raise ValueError('模型中应有一台 Odin 和一台 Livox 安装参考件')


def compact(grid_triangles):
    """顶点已对齐毫米网格；删除共线、重复的三角面。"""
    xyz = grid_triangles.reshape(-1, 3)
    vertices, indices = np.unique(xyz, axis=0, return_inverse=True)
    triangles = indices.reshape(-1, 3)
    xyz = vertices[triangles]
    normals = np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0])
    triangles = triangles[np.any(normals != 0, axis=1)]
    _, first = np.unique(np.sort(triangles, axis=1), axis=0, return_index=True)
    return vertices, triangles[np.sort(first)]


def iter_component_meshes(assembly):
    """按原总装零位给出各显示零件，顶点坐标单位为毫米。"""
    raw = assembly.read_bytes()
    if sha256(raw).hexdigest() != ASSEMBLY_SHA256:
        print('总装版本已改变，轮心和安装坐标仍按原版导出，请核对新装配。', file=sys.stderr)
    blocks = read_blocks(raw)
    entries = read_directory(find_block(blocks, 'FaceTessellations/Directory').inflate())
    directory = {instance_path(entry.name): entry for entry in entries}
    by_id = {entry.id: entry for entry in entries}
    placements = defaultdict(list)
    part_meshes = {}
    for path, group, transform in active_instances(blocks):
        entry = directory[path]
        # 多个实例可能共用同一份显示网格。
        seen = set()
        while not entry.chunk:
            if entry.id in seen:
                raise ValueError(f'循环的显示网格引用：{path}')
            seen.add(entry.id)
            if entry.alias not in by_id:
                part = path.rsplit('/', 1)[-1].rsplit('-', 1)[0]
                filename = assembly.with_name(part + '.SLDPRT')
                local = read_saved_mesh(read_blocks(filename.read_bytes()))
                if local is None:
                    if part not in {'零件2', '零件3'}:
                        raise ValueError(f'缺少零件的显示网格：{path}')
                    print(f'无可显示面：{filename.name}（总装及零件缓存均无网格）')
                    break
                part_meshes[entry.id] = local
                break
            entry = by_id[entry.alias]
        if not entry.chunk and entry.id not in part_meshes:
            continue
        placements[entry.id].append((group, transform))

    chunks = defaultdict(list)
    for key in placements:
        entry = by_id[key]
        chunks[entry.chunk].append(entry)
    for chunk, chunk_entries in chunks.items():
        meshes = _component_meshes(blocks, chunk_entries) if chunk else part_meshes
        for entry in chunk_entries:
            mesh = meshes[entry.id]
            vertices = np.asarray(mesh.vertices)
            indices = np.asarray(mesh.triangles, dtype=np.int32)
            for group, transform in placements[entry.id]:
                # SolidWorks 的平移为米，缓存网格为毫米。
                rotation = CAD_TO_ROS @ transform[:3, :3]
                translation = CAD_TO_ROS @ transform[:3, 3] - ORIGINS[group]
                points_mm = vertices @ rotation.T + translation * 1000
                faces = indices[:, ::-1] if np.linalg.det(rotation) < 0 else indices
                yield group, points_mm, faces


def export(assembly, output, grid_mm):
    triangles_by_group = defaultdict(list)
    for group, points_mm, faces in iter_component_meshes(assembly):
        step_mm = min(grid_mm, 1.0) if group == 'sentry_odin1_lite' else grid_mm
        grid = np.rint(points_mm / step_mm).astype(np.int32)
        verts, faces = compact(grid[faces])
        if len(faces):
            triangles_by_group[group].append(verts[faces])

    output.mkdir(parents=True, exist_ok=True)
    if set(triangles_by_group) != set(ORIGINS):
        raise ValueError('总装未能分出底盘、上部和四个车轮')
    with TemporaryDirectory(dir=output) as temp:
        for group in ORIGINS:
            vertices, triangles = compact(np.concatenate(triangles_by_group[group]))
            step_mm = min(grid_mm, 1.0) if group == 'sentry_odin1_lite' else grid_mm
            metres = vertices * (step_mm * 0.001)
            bounds = metres[triangles.ravel()]
            if not len(bounds) or not np.isfinite(bounds).all() or np.max(np.abs(bounds)) > 0.9:
                raise ValueError(f'{group} 的尺寸异常，检查坐标或视场显示体')
            count = write_stl(Path(temp) / f'{group}.stl', metres, triangles)
            print(f'{group}: {count} faces, min {bounds.min(0)}, max {bounds.max(0)}')
        for group in ORIGINS:
            name = group + '.stl'
            (Path(temp) / name).replace(output / name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('assembly', type=Path)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1]
                        / 'src/sentry_description/meshes')
    parser.add_argument('--grid-mm', type=float, default=3.0, help='显示网格简化步距（毫米）')
    args = parser.parse_args()
    if not 1 <= args.grid_mm <= 5:
        parser.error('--grid-mm 须在 1 到 5 之间')
    export(args.assembly, args.output, args.grid_mm)
