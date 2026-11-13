#!/usr/bin/env python3
"""把官方 RMUL 场地 STEP 转成 Gazebo 场地资产（launch 启动时自动调用）。

1. STEP → 场地坐标（Z 向上、内场西南角为原点、单位米）→ 带材质的 DAE；
2. 从三角网格量出各高度层，反推出矩形碰撞盒；
3. 写出 model.sdf / model.config / field_stats.json。

配色沿用改造前的场地：顶面用 official_top.png 贴图，0.20 m 平台整块绿，
0.40 m 平台侧面浅蓝，围挡深灰 + 2 cm 白压顶，其余深灰。

依赖 cascadio / trimesh（pip 装），numpy 由 ROS 提供：
    python3 -m pip install --user cascadio trimesh
"""
import argparse
import io
import json
import shutil
import sys
from pathlib import Path

import numpy as np

# 场地坐标约定：内场 12 × 8 m，西南角为原点；围挡外扩 0.3 m
FIELD_W, FIELD_H = 12.0, 8.0
WALL = 0.3
OUTER_W, OUTER_H = FIELD_W + 2 * WALL, FIELD_H + 2 * WALL
BASE_Z = -0.1
WALL_TOP = 0.40
TEXTURE_REL = '../materials/textures/official_top.png'
TEXTURE_NAME = 'official_top.png'

PALETTE = {
    'mat_dark': (0.20, 0.20, 0.20),
    'mat_white': (1.0, 1.0, 1.0),
    'mat_lightblue': (0.8784, 0.9490, 1.0),
    'mat_red': (1.0, 0.0, 0.0),
    'mat_blue': (0.0, 0.0078, 1.0),
    'mat_green': (0.0, 1.0, 0.0),
}
MAT_ORDER = ['mat_dark', 'mat_paper', 'mat_white', 'mat_lightblue',
             'mat_red', 'mat_blue', 'mat_green']


def _require_deps():
    """cascadio 是 OpenCASCADE 的 Python 封装，只能 pip 装；缺了就给出明确命令。"""
    try:
        import cascadio  # noqa: F401
        import trimesh    # noqa: F401
    except ImportError as error:
        raise SystemExit(
            f'缺少 STEP 解析依赖：{error.name or error}\n'
            '请先安装：python3 -m pip install --user cascadio trimesh\n'
            '（cascadio 自带 OpenCASCADE，不需要另外装 CAD 软件）')


def to_field(v):
    """STEP（+Y 朝下、原点在中心、米）→ 场地坐标（Z 向上、内场西南角为原点）。"""
    return np.stack([-v[:, 0] + FIELD_W / 2, -v[:, 2] + FIELD_H / 2, -v[:, 1]], axis=1)


def load_step(path, tol):
    import cascadio
    import trimesh
    glb = cascadio.load(Path(path).read_bytes(), file_type='step',
                        tol_linear=tol, merge_primitives=True)
    scene = trimesh.load(io.BytesIO(glb), file_type='glb', force='scene')
    parts = {}
    for name, geom in scene.geometry.items():
        parts[name] = (to_field(np.asarray(geom.vertices, float)),
                       np.asarray(geom.faces, np.int64))
    return parts


def face_normals_z(tris):
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    ln = np.linalg.norm(n, axis=1)
    ln[ln == 0] = 1
    return n[:, 2] / ln


def materials_for(name, tris):
    """按实体角色上色，复刻改造前场地的观感。"""
    nz = face_normals_z(tris)
    z = tris[:, :, 2].mean(1)
    up = nz > 0.9
    out = np.full(len(tris), 'mat_dark', dtype=object)
    if name == 'SOLID_6':            # 0.20 m 平台整块绿
        out[:] = 'mat_green'
    elif name == 'SOLID_2':          # 红队角标
        out[:] = 'mat_red'
    elif name == 'SOLID_5':          # 蓝队角标
        out[:] = 'mat_blue'
    elif name == 'SHELL':            # 围挡压顶
        out[:] = 'mat_white'
    elif name == 'SOLID_4':          # 围挡：整块深灰，只留 SHELL 的 2 cm 白压顶
        out[:] = 'mat_dark'
    elif name == 'SOLID_3':          # 0.40 m 平台：顶贴图、侧面浅蓝
        out[up] = 'mat_paper'
        out[np.abs(nz) <= 0.9] = 'mat_lightblue'
    else:                            # 地台与地面标记：顶面贴图
        out[up & (z < 0.35)] = 'mat_paper'
        out[up & (z >= 0.35)] = 'mat_white'
    return out


def write_dae(path, groups):
    pos, nrm, tex, blocks = [], [], [], []
    for mat, tri, uv in groups:
        offset = sum(len(b[1]) * 3 for b in blocks)
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        ln = np.linalg.norm(n, axis=1)
        ln[ln == 0] = 1
        n = (n / ln[:, None])[:, None, :].repeat(3, axis=1)
        pos.append(tri.reshape(-1, 3))
        nrm.append(n.reshape(-1, 3))
        tex.append(uv.reshape(-1, 2) if uv is not None
                   else np.zeros((len(tri) * 3, 2)))
        idx = np.arange(offset, offset + len(tri) * 3).reshape(-1, 3)
        blocks.append((mat, idx, uv is not None))

    pos = np.concatenate(pos)
    nrm = np.concatenate(nrm)
    uv = np.concatenate(tex)

    def arr(values):
        return ' '.join(f'{v:.6g}' for v in np.asarray(values).ravel())

    mats = [g[0] for g in groups]
    out = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1">',
        '  <asset>',
        '    <contributor><authoring_tool>rm_arena.step_to_field</authoring_tool></contributor>',
        '    <created>2026-11-02T00:00:00</created>',
        '    <modified>2026-11-02T00:00:00</modified>',
        '    <unit name="meter" meter="1"/>',
        '    <up_axis>Z_UP</up_axis>',
        '  </asset>',
        '  <library_images>',
        f'    <image id="official_top"><init_from>{TEXTURE_REL}</init_from></image>',
        '  </library_images>',
        '  <library_effects>',
    ]
    for mat in mats:
        if mat == 'mat_paper':
            out += [
                f'    <effect id="{mat}-effect"><profile_COMMON>',
                '      <newparam sid="paper-surface"><surface type="2D">',
                '        <init_from>official_top</init_from></surface></newparam>',
                '      <newparam sid="paper-sampler"><sampler2D>',
                '        <source>paper-surface</source></sampler2D></newparam>',
                '      <technique sid="common"><phong>',
                '        <diffuse><texture texture="paper-sampler" texcoord="UVSET0"/></diffuse>',
                '        <specular><color>0 0 0 1</color></specular>',
                '        <shininess><float>1</float></shininess>',
                '      </phong></technique>',
                '    </profile_COMMON></effect>',
            ]
            continue
        r, g, b = PALETTE[mat]
        out += [
            f'    <effect id="{mat}-effect"><profile_COMMON><technique sid="common"><phong>',
            f'      <diffuse><color>{r} {g} {b} 1</color></diffuse>',
            '      <specular><color>0 0 0 1</color></specular>',
            '      <shininess><float>1</float></shininess>',
            '    </phong></technique></profile_COMMON></effect>',
        ]
    out.append('  </library_effects>')
    out.append('  <library_materials>')
    for mat in mats:
        out.append(f'    <material id="{mat}" name="{mat}">'
                   f'<instance_effect url="#{mat}-effect"/></material>')
    out.append('  </library_materials>')
    out += [
        '  <library_geometries>',
        '    <geometry id="field" name="field"><mesh>',
        f'      <source id="pos"><float_array id="pos-array" count="{pos.size}">{arr(pos)}</float_array>',
        f'        <technique_common><accessor source="#pos-array" count="{len(pos)}" stride="3">',
        '          <param name="X" type="float"/><param name="Y" type="float"/>',
        '          <param name="Z" type="float"/>',
        '        </accessor></technique_common></source>',
        f'      <source id="nrm"><float_array id="nrm-array" count="{nrm.size}">{arr(nrm)}</float_array>',
        f'        <technique_common><accessor source="#nrm-array" count="{len(nrm)}" stride="3">',
        '          <param name="X" type="float"/><param name="Y" type="float"/>',
        '          <param name="Z" type="float"/>',
        '        </accessor></technique_common></source>',
        f'      <source id="uv"><float_array id="uv-array" count="{uv.size}">{arr(uv)}</float_array>',
        f'        <technique_common><accessor source="#uv-array" count="{len(uv)}" stride="2">',
        '          <param name="S" type="float"/><param name="T" type="float"/>',
        '        </accessor></technique_common></source>',
        '      <vertices id="verts"><input semantic="POSITION" source="#pos"/></vertices>',
    ]
    for mat, idx, _ in blocks:
        out.append(f'      <triangles material="{mat}" count="{len(idx)}">')
        out.append('        <input semantic="VERTEX" source="#verts" offset="0"/>')
        out.append('        <input semantic="NORMAL" source="#nrm" offset="0"/>')
        out.append('        <input semantic="TEXCOORD" source="#uv" offset="0" set="0"/>')
        out.append('        <p>' + ' '.join(str(v) for v in idx.ravel()) + '</p>')
        out.append('      </triangles>')
    out += ['    </mesh></geometry>', '  </library_geometries>',
            '  <library_visual_scenes>', '    <visual_scene id="Scene" name="Scene">',
            '      <node id="field" name="field"><instance_geometry url="#field"/></node>',
            '    </visual_scene>', '  </library_visual_scenes>',
            '  <scene><instance_visual_scene url="#Scene"/></scene>', '</COLLADA>']
    Path(path).write_text('\n'.join(out) + '\n', encoding='utf-8')


def height_columns(tris, res=0.05):
    """把水平面按格子取最高点，得到 (nx, ny) 高度场。"""
    nx = int(round(OUTER_W / res))
    ny = int(round(OUTER_H / res))
    hm = np.zeros((nx, ny))
    nz = face_normals_z(tris)
    for t in tris[np.abs(nz) > 0.9]:
        z = t[:, 2].mean()
        lo = np.floor((t[:, :2].min(0) + WALL) / res).astype(int)
        hi = np.ceil((t[:, :2].max(0) + WALL) / res).astype(int)
        lo = np.clip(lo, 0, [nx - 1, ny - 1])
        hi = np.clip(hi, 0, [nx - 1, ny - 1])
        block = hm[lo[0]:hi[0] + 1, lo[1]:hi[1] + 1]
        hm[lo[0]:hi[0] + 1, lo[1]:hi[1] + 1] = np.maximum(block, z)
    return hm, res


def greedy_rects(mask):
    """把布尔掩膜贪心拆成矩形，返回 (i0, j0, di, dj)。"""
    m = mask.copy()
    nx, ny = m.shape
    out = []
    for i in range(nx):
        for j in range(ny):
            if not m[i, j]:
                continue
            di = 1
            while i + di < nx and m[i + di, j]:
                di += 1
            dj = 1
            while j + dj < ny and m[i:i + di, j + dj].all():
                dj += 1
            out.append((i, j, di, dj))
            m[i:i + di, j:j + dj] = False
    return out


def collision_boxes(hm, res):
    """地台一块、围挡四条、场内平台按实测高度逐块生成封闭碰撞盒。"""
    nx, ny = hm.shape
    xs = np.arange(nx) * res - WALL
    ys = np.arange(ny) * res - WALL
    inside = ((xs >= 0) & (xs <= FIELD_W))[:, None] & \
             ((ys >= 0) & (ys <= FIELD_H))[None, :]

    cx, cy = FIELD_W / 2, FIELD_H / 2
    boxes = [{
        'size': [round(OUTER_W, 3), round(OUTER_H, 3), round(-BASE_Z, 3)],
        'pose': [round(cx, 3), round(cy, 3), round(BASE_Z / 2, 3)],
        'top': 0.0,
    }]

    wall_cells = (~inside) & (hm > 0.02)
    wall_h = round(float(hm[wall_cells].max()), 2) if wall_cells.any() else WALL_TOP
    for name, size, pose in [
        ('south', [OUTER_W, WALL, wall_h], [cx, -WALL / 2, wall_h / 2]),
        ('north', [OUTER_W, WALL, wall_h], [cx, FIELD_H + WALL / 2, wall_h / 2]),
        ('west', [WALL, FIELD_H, wall_h], [-WALL / 2, cy, wall_h / 2]),
        ('east', [WALL, FIELD_H, wall_h], [FIELD_W + WALL / 2, cy, wall_h / 2]),
    ]:
        boxes.append({'size': [round(v, 3) for v in size],
                      'pose': [round(v, 3) for v in pose],
                      'top': wall_h, 'part': f'wall_{name}'})

    inner = inside & (hm > 0.02)
    levels = sorted({round(float(v), 2) for v in np.unique(np.round(hm[inner], 2))},
                    reverse=True)
    remaining = inner.copy()
    for level in levels:
        mask = remaining & (np.abs(hm - level) < 0.005)
        for i, j, di, dj in greedy_rects(mask):
            x0, y0 = i * res - WALL, j * res - WALL
            boxes.append({
                'size': [round(di * res, 3), round(dj * res, 3), round(level, 3)],
                'pose': [round(x0 + di * res / 2, 3), round(y0 + dj * res / 2, 3),
                         round(level / 2, 3)],
                'top': level,
            })
            remaining[i:i + di, j:j + dj] = False
    return boxes


def write_sdf(path, boxes):
    lines = [
        "<?xml version='1.0' encoding='utf-8'?>",
        '<sdf version="1.6">',
        '  <!-- 由 rm_arena.step_to_field 从官方 STEP 生成，改尺寸请改脚本后重跑。 -->',
        '  <model name="rmul_2027">',
        '    <static>true</static>',
        '    <link name="arena">',
        '      <visual name="field_visual">',
        '        <geometry>',
        '          <mesh>',
        '            <uri>model://rmul_2027/meshes/field.dae</uri>',
        '          </mesh>',
        '        </geometry>',
        '      </visual>',
    ]
    for k, box in enumerate(boxes):
        sx, sy, sz = box['size']
        px, py, pz = box['pose']
        lines += [
            f'      <collision name="c{k:02d}_h{box["top"]:.2f}">',
            f'        <pose>{px} {py} {pz} 0 0 0</pose>',
            '        <geometry>',
            f'          <box><size>{sx} {sy} {sz}</size></box>',
            '        </geometry>',
            '        <surface><friction><ode><mu>0.9</mu><mu2>0.9</mu2>'
            '</ode></friction></surface>',
            '      </collision>',
        ]
    lines += ['    </link>', '  </model>', '</sdf>']
    Path(path).write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return len(boxes)


MODEL_CONFIG = """<?xml version="1.0"?>
<model>
  <name>RMUL 2027 3v3</name>
  <version>2.0</version>
  <sdf version="1.6">model.sdf</sdf>
  <author><name>Official STEP converted by rm_arena.step_to_field</name></author>
  <description>
    官方 STEP 场地：内场 12 × 8 m，围挡外扩 0.3 m、高 0.42 m；视觉为
    meshes/field.dae（俯视贴图 + 现有配色），碰撞为按实测高度生成的封闭盒。
    尺寸与统计见 meshes/field_stats.json。
  </description>
</model>
"""


def convert(step, out, tol=1.0, texture_source=None):
    """跑完整转换，返回统计字典；失败抛异常。"""
    _require_deps()
    out = Path(out)
    (out / 'meshes').mkdir(parents=True, exist_ok=True)
    texture = out / 'materials' / 'textures' / TEXTURE_NAME
    if not texture.is_file():
        if texture_source and Path(texture_source).is_file():
            texture.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(texture_source, texture)
        else:
            raise FileNotFoundError(
                f'缺少场地贴图 {texture}，请用 --texture-source 指定 {TEXTURE_NAME}')

    parts = load_step(step, tol)
    tris_by_part = {name: v[f] for name, (v, f) in parts.items()}
    ordered = sorted(tris_by_part)
    all_tris = np.concatenate([tris_by_part[name] for name in ordered])
    mats = np.concatenate([materials_for(name, tris_by_part[name]) for name in ordered])

    groups = []
    for mat in MAT_ORDER:
        sel = mats == mat
        if not sel.any():
            continue
        tri = all_tris[sel]
        uv = None
        if mat == 'mat_paper':
            xy = tri[:, :, :2].reshape(-1, 2)
            uv = np.stack([xy[:, 0] / FIELD_W, xy[:, 1] / FIELD_H],
                          axis=1).reshape(-1, 3, 2)
        groups.append((mat, tri, uv))

    write_dae(out / 'meshes' / 'field.dae', groups)
    hm, res = height_columns(all_tris)
    boxes = collision_boxes(hm, res)
    count = write_sdf(out / 'model.sdf', boxes)
    if not (out / 'model.config').is_file():
        (out / 'model.config').write_text(MODEL_CONFIG, encoding='utf-8')

    stats = {
        'source': str(Path(step).resolve()),
        'triangles': int(len(all_tris)),
        'parts': {k: int(len(v)) for k, v in parts.items()},
        'materials': {m: int((mats == m).sum()) for m in MAT_ORDER if (mats == m).any()},
        'collision_boxes': boxes,
        'extent': {'x': [0.0, OUTER_W], 'y': [0.0, OUTER_H], 'z': [BASE_Z, WALL_TOP]},
    }
    (out / 'meshes' / 'field_stats.json').write_text(json.dumps(stats, indent=1),
                                                     encoding='utf-8')
    stats['collision_count'] = count
    stats['out'] = str(out)
    return stats


def main(argv=None):
    parser = argparse.ArgumentParser(description='官方 STEP → Gazebo 场地资产')
    parser.add_argument('--step', required=True, help='RMUL2027_3V3_V1.0.0.stp 之类')
    parser.add_argument('--out', required=True, help='模型目录（含 meshes/）')
    parser.add_argument('--tol', type=float, default=1.0, help='三角化弦差 mm')
    parser.add_argument('--texture-source', default=None,
                        help='场地贴图模板路径（out 里没有时复制）')
    args = parser.parse_args(argv)
    stats = convert(args.step, args.out, args.tol, args.texture_source)
    print(f"场地已生成：{stats['out']}")
    print(f"  三角面 {stats['triangles']}，碰撞盒 {stats['collision_count']}")
    print(f"  范围 x{stats['extent']['x']} y{stats['extent']['y']} z{stats['extent']['z']}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
