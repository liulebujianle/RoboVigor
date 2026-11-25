"""按 CAD 零件的保存姿态生成机械参考系。"""
import math
from pathlib import Path

import numpy as np
import yaml


def recover_frames(parts, pivot_z):
    """读取零件姿态，记录来源和坐标轴约定。"""
    visible = [p for p in parts if not p.hidden]
    conversion = np.eye(4)
    conversion[:3, :3] = [[1, 0, 0], [0, 0, -1], [0, 1, 0]]

    def unique(fragment):
        found = [p for p in visible if fragment in p.name.rsplit('/', 1)[-1]]
        if len(found) != 1:
            raise RuntimeError(f'Expected one {fragment} CAD instance, found {len(found)}')
        return found[0]

    def transform(part):
        return conversion @ np.array(part.transform).reshape(4, 4).T

    def vertices(part):
        return np.asarray(part.mesh.vertices)[:, [0, 2, 1]] * [0.001, -0.001, 0.001]

    def text(v):
        return ' '.join(f'{float(x):.12g}' for x in v)

    def rpy(rotation):
        return [math.atan2(rotation[2, 1], rotation[2, 2]),
                math.atan2(-rotation[2, 0], math.hypot(rotation[0, 0], rotation[1, 0])),
                math.atan2(rotation[1, 0], rotation[0, 0])]

    frames = {}

    def add(name, parent, position, rotation, source, convention):
        frames[name] = dict(parent=parent, xyz=text(position), rpy=text(rpy(rotation)),
                            source=source, convention=convention)

    pivot = np.array([0., 0., pivot_z])
    for number, name in [(1, 'lidar_link'), (2, 'lidar_aux_link')]:
        part = unique(f'mid-360-asm（带范围）V2.001-{number}@')
        matrix = transform(part)
        # 这份雷达 CAD 的局部 Y 轴指向扫描半球上方。
        rotation = matrix[:3, :3] @ np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]])
        add(name, 'gimbal_yaw_link', matrix[:3, 3] - pivot, rotation, part.name,
            'CAD origin; x=CAD X, y=-CAD Z, z=CAD Y (hardware-up); driver extrinsics uncalibrated')
    return dict(units='metres/radians', status='CAD nominal mechanical frames; calibrate before hardware use',
                frames=frames)


def write_frames(description, data):
    """把参考系写到 config/frames.yaml，供 sensors.xacro 加载。"""
    target = Path(description) / 'config'
    target.mkdir(parents=True, exist_ok=True)
    (target / 'frames.yaml').write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False))
