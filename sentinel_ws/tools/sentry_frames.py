"""Recover mechanical reference frames from the saved native CAD instances."""
import math
from pathlib import Path

import numpy as np
import yaml


def recover_frames(parts, pivot_z):
    """Use current CAD poses, retaining source names and frame-axis conventions."""
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
        # This CAD uses local Y as the scan hemisphere's up axis.
        rotation = matrix[:3, :3] @ np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]])
        add(name, 'gimbal_yaw_link', matrix[:3, 3] - pivot, rotation, part.name,
            'CAD origin; x=CAD X, y=-CAD Z, z=CAD Y (hardware-up); driver extrinsics uncalibrated')
    camera = unique('MV-CS004-10UMUC相机3103-1@')
    matrix = transform(camera)
    # Camera/lens points toward negative CAD Z. Keep body REP-103 axes.
    axes = np.array([[0, -1, 0], [0, 0, 1], [-1, 0, 0]])
    add('camera_link', 'gimbal_yaw_link', matrix[:3, 3] - pivot, matrix[:3, :3] @ axes,
        camera.name, 'CAD camera origin; x forward along lens, y left, z up; optical center uncalibrated')
    optical = np.array([[0, 0, 1], [-1, 0, 0], [0, -1, 0]])
    add('camera_optical_frame', 'camera_link', np.zeros(3), optical, camera.name,
        'x right, y down, z forward; coincident nominal CAD origin, not a measured optical center')
    speed_module = unique('23RM步兵-02.01.0002(裁判系统测速模块SM01)-1@')
    ball = unique('16.6小弹丸-1@')
    matrix = transform(speed_module)
    rotation = matrix[:3, :3] @ axes
    center = (vertices(ball).min(0) + vertices(ball).max(0)) / 2
    add('gun_link', 'gimbal_yaw_link', center - pivot, rotation, speed_module.name + '; ' + ball.name,
        'CAD projectile center; x along firing passage (-speed-module CAD Z), y left, z up')
    forward = rotation[:, 0]
    distance = float(np.max(vertices(speed_module) @ forward) - center @ forward)
    if not 0 < distance < .3:
        raise RuntimeError(f'Muzzle plane is inconsistent with the CAD firing direction: {distance}')
    add('muzzle_link', 'gun_link', [distance, 0., 0.], np.eye(3), speed_module.name,
        'Firing-axis intersection with the foremost CAD speed-module plane; nominal mechanical exit')
    return dict(units='metres/radians', status='CAD nominal mechanical frames; calibrate before hardware use',
                frames=frames)


def write_frames(description, data):
    """Installable editable YAML is loaded explicitly by sensors.xacro."""
    target = Path(description) / 'config'
    target.mkdir(parents=True, exist_ok=True)
    (target / 'frames.yaml').write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False))
