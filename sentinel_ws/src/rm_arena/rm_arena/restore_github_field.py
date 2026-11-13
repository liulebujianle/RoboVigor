#!/usr/bin/env python3
"""从随包归档的 GitHub 场地恢复材质与实体碰撞，仅修复 DAE 加载兼容性。"""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

COMMIT = 'e2ddcdb1ebbef47eaeae3490fe0c897d69083659'
URI = 'http://www.collada.org/2005/11/COLLADASchema'
NS = {'c': URI}


def restore(out):
    """不联网，使用 source/ 中的固定版本；不改变其他 ROS 包或启动参数。"""
    out = Path(out)
    reference = out / 'source'
    tree = ET.parse(reference / 'github_field.dae')
    root = tree.getroot()
    ET.register_namespace('', URI)

    # 原文件将 VERTEX/NORMAL/TEXCOORD 都设为 offset=0。
    # 为 Gazebo Classic 显式展开交错索引，不改变顶点、法线、UV 或材质。
    for faces in root.findall('.//c:triangles', NS):
        inputs = faces.findall('c:input', NS)
        offsets = [int(item.get('offset', '0')) for item in inputs]
        stride = max(offsets) + 1
        indices = list(map(int, faces.findtext('c:p', namespaces=NS).split()))
        count = int(faces.get('count')) * 3
        if len(indices) != count * stride:
            raise ValueError('参考 DAE 的三角形索引长度不正确')
        expanded = [indices[i * stride + offset] for i in range(count) for offset in offsets]
        for offset, item in enumerate(inputs):
            item.set('offset', str(offset))
        faces.find('c:p', NS).text = ' '.join(map(str, expanded))

    # 已核对该提交的 mat_white 正好是 155 面向内的封闭围挡压顶。
    # 反转整个压顶，不移动顶点、UV，也不改变任何材质数值。
    white = next(e for e in root.findall('.//c:triangles', NS) if e.get('material') == 'mat_white')
    if int(white.get('count')) != 155:
        raise ValueError('参考版本的围挡压顶与固定提交不一致')
    inputs = white.findall('c:input', NS)
    stride = len(inputs)
    n_offset = next(int(e.get('offset')) for e in inputs if e.get('semantic') == 'NORMAL')
    values = list(map(int, white.findtext('c:p', namespaces=NS).split()))
    normal_indices = set(values[n_offset::stride])
    corrected = []
    for start in range(0, len(values), 3 * stride):
        for vertex in (0, 2, 1):
            corrected.extend(values[start + vertex * stride:start + (vertex + 1) * stride])
    white.find('c:p', NS).text = ' '.join(map(str, corrected))
    normal_source = next(e.get('source')[1:] for e in inputs if e.get('semantic') == 'NORMAL')
    source = next(e for e in root.findall('.//c:source', NS) if e.get('id') == normal_source)
    array = source.find('c:float_array', NS)
    normals = list(map(float, array.text.split()))
    for index in normal_indices:
        normals[index * 3:index * 3 + 3] = [-v for v in normals[index * 3:index * 3 + 3]]
    array.text = ' '.join(f'{v:.9g}' for v in normals)

    # geometry 和 node 原本重复使用 field ID，保留几何引用，只改 node ID。
    for node in root.findall('.//c:node', NS):
        if node.get('id') == 'field':
            node.set('id', 'field-node')
    geometry = root.find('.//c:geometry', NS)
    symbols = sorted({faces.get('material') for faces in geometry.findall('.//c:triangles', NS)})
    material_ids = {item.get('id') for item in root.findall('.//c:material', NS)}
    if not set(symbols) <= material_ids:
        raise ValueError('参考 DAE 的材质引用不完整')
    for instance in root.findall('.//c:instance_geometry', NS):
        for previous in instance.findall('c:bind_material', NS):
            instance.remove(previous)
        bindings = ET.SubElement(ET.SubElement(instance, f'{{{URI}}}bind_material'),
                                 f'{{{URI}}}technique_common')
        for symbol in symbols:
            binding = ET.SubElement(bindings, f'{{{URI}}}instance_material',
                                    symbol=symbol, target=f'#{symbol}')
            if symbol == 'mat_paper':
                ET.SubElement(binding, f'{{{URI}}}bind_vertex_input', semantic='UVSET0',
                              input_semantic='TEXCOORD', input_set='0')
    ids = [item.get('id') for item in root.iter() if item.get('id')]
    if len(ids) != len(set(ids)):
        raise ValueError('DAE 包含重复 ID')
    for image in root.findall('.//c:image/c:init_from', NS):
        if not (out / 'meshes' / image.text).is_file():
            raise FileNotFoundError(f'场地贴图缺失：{image.text}')

    model_data = (reference / 'github_model.sdf').read_bytes()
    model = ET.fromstring(model_data)
    boxes = model.findall('.//collision/geometry/box/size')
    if model.findtext('.//static') != 'true' or len(boxes) != 29:
        raise ValueError('GitHub 固定版本应有 29 个静态实体碰撞盒')
    ET.indent(tree)
    tree.write(out / 'meshes/field.dae', encoding='utf-8', xml_declaration=True)
    (out / 'model.sdf').write_bytes(model_data)
    (out / 'model.config').write_bytes((reference / 'github_model.config').read_bytes())
    stats = json.loads((reference / 'github_field_stats.json').read_text(encoding='utf-8'))
    # 旧统计中的平面范围有误；从实际参考几何计算，禁止移动车体坐标系来迁就统计。
    values = list(map(float, root.findall('.//c:float_array', NS)[0].text.split()))
    stats['extent'] = {axis: [min(values[i::3]), max(values[i::3])]
                       for i, axis in enumerate('xyz')}
    stats.update({
        'source': 'https://github.com/liulebujianle/RoboVigor', 'github_commit': COMMIT,
        'palette_source': 'sentinel_ws/src/rm_arena/rm_arena/step_to_field.py',
        'collision': '29 closed boxes, exact GitHub model.sdf',
        'reference_sdf_sha256': hashlib.sha256(model_data).hexdigest(),
        'visual_repairs': ['separate input offsets', 'explicit material/UV bindings',
                           'unique node ID', '155 inward white rim faces reversed'],
    })
    (out / 'meshes/field_stats.json').write_text(
        json.dumps(stats, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return stats


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, help='含 source/github_* 归档的模型目录')
    args = parser.parse_args(argv)
    try:
        result = restore(args.out)
    except (OSError, ValueError, ET.ParseError) as error:
        parser.exit(1, f'恢复场地失败：{error}\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
