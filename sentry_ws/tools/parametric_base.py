"""生成导航模型的底盘和四个全向轮。几何尺寸以毫米为单位，输出 DAE 使用米。"""
import argparse
import math
from pathlib import Path

import numpy as np


def loft(rings, *, hollow=False):
    """自下而上连接等长、逆时针排列的轮廓；中空零件的最后一圈接回第一圈。"""
    count = len(rings[0])
    vertices = np.vstack(rings)
    faces = []
    for i in range(len(rings) if hollow else len(rings) - 1):
        row = i * count
        next_row = ((i + 1) % len(rings)) * count
        for j in range(count):
            k = (j + 1) % count
            faces.extend(((row + j, row + k, next_row + k), (row + j, next_row + k, next_row + j)))
    if not hollow:
        bottom, top = len(vertices), len(vertices) + 1
        vertices = np.vstack((vertices, rings[0].mean(0), rings[-1].mean(0)))
        last = (len(rings) - 1) * count
        for j in range(count):
            k = (j + 1) % count
            faces.extend(((bottom, k, j), (top, last + j, last + k)))
    return vertices, np.array(faces)


def rounded_contour(corners, trim, segments=5):
    corners = np.asarray(corners, dtype=float)
    points = []
    for i, corner in enumerate(corners):
        before = corners[i - 1] - corner
        after = corners[(i + 1) % len(corners)] - corner
        start = corner + trim * before / np.linalg.norm(before)
        end = corner + trim * after / np.linalg.norm(after)
        for t in np.linspace(0, 1, segments + 1):
            points.append((1 - t)**2 * start + 2 * t * (1 - t) * corner + t**2 * end)
    return np.asarray(points)


def layer(xy, z):
    return np.column_stack((xy, np.full(len(xy), z)))


def rounded_box(depth, width, height, corner, bevel):
    def outline(inset):
        x, y = depth / 2 - inset, width / 2 - inset
        corners = [(x, y), (-x, y), (-x, -y), (x, -y)]
        return rounded_contour(corners, min(corner, x * 0.8, y * 0.8))

    outer, inner = outline(0), outline(bevel)
    half = height / 2
    return loft([layer(inner, -half), layer(outer, -half + bevel),
                 layer(outer, half - bevel), layer(inner, half)])


def rotate_z(angle):
    c, s = math.cos(angle), math.sin(angle)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def rotate_y(angle):
    c, s = math.cos(angle), math.sin(angle)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def placed(mesh, rotation=None, offset=(0, 0, 0)):
    vertices, faces = mesh
    if rotation is not None:
        vertices = vertices @ rotation.T
    return vertices + offset, faces


def bumper():
    outline = rounded_contour(
        [(267, 91), (91, 267), (-91, 267), (-267, 91),
         (-267, -91), (-91, -267), (91, -267), (267, -91)], 32, 8)
    profile = [(0.991, -18), (1, -15), (1, -6), (0.990, -3),
               (0.962, -3), (0.954, -6), (0.954, -15), (0.962, -18)]
    return loft([layer(outline * scale, z) for scale, z in profile], hollow=True)


def chassis():
    pieces = [bumper(),
              placed(rounded_box(249, 249, 38, 42, 4), offset=(0, 0, -2)),
              placed(rounded_box(216, 216, 8, 39, 2), offset=(0, 0, 20))]
    for i in range(4):
        radial = rotate_z(i * math.pi / 2)
        diagonal = rotate_z(i * math.pi / 2 + math.pi / 4)
        guard = placed(rounded_box(28, 135, 93, 10, 4), rotate_y(-0.17), (221, 0, 66))
        pieces.append(placed(guard, radial))
        for lateral in (-53, 53):
            rail = placed(rounded_box(127, 13, 24, 5, 2), offset=(183, lateral, 1))
            pieces.append(placed(rail, radial))
        arm = placed(rounded_box(79, 32, 36, 9, 3), offset=(169, 0, -24))
        upright = placed(rounded_box(32, 31, 66, 7, 3), offset=(186, 0, -48))
        pieces.extend([placed(arm, diagonal), placed(upright, diagonal)])
    return pieces


def radial_surface(profile, segments=40, hollow=False):
    angle = np.arange(segments) * 2 * math.pi / segments
    circle = np.column_stack((np.cos(angle), np.sin(angle)))
    return loft([layer(radius * circle, z) for radius, z in profile], hollow=hollow)


def roller():
    angle = np.arange(12) * 2 * math.pi / 12
    section = np.column_stack((9.3 * np.cos(angle), 8.0 * np.sin(angle)))
    profile = [(-15.4, 0.33), (-13.5, 0.72), (-9, 0.94), (0, 1),
               (9, 0.94), (13.5, 0.72), (15.4, 0.33)]
    return loft([layer(section * scale, z) for z, scale in profile])


def wheel(yaw):
    hub = [(12, -19.9), (14, -18.2), (16, -12), (16, 12), (14, 18.2), (12, 19.9)]
    rim = [(59, -2.6), (60.5, -1.4), (60.5, 1.4), (59, 2.6),
           (48, 2.6), (47, 1.4), (47, -1.4), (48, -2.6)]
    pieces = [radial_surface(hub)]
    tread = roller()
    for side in (-1, 1):
        z = side * 13.8
        pieces.append(placed(radial_surface(rim, hollow=True), offset=(0, 0, z)))
        for j in range(5):
            spoke = placed(rounded_box(42, 10, 4.4, 3.4, 1), offset=(32, 0, z))
            pieces.append(placed(spoke, rotate_z(2 * math.pi * j / 5)))
        # 轮缘两排各 14 个鼓形滚子，错开半格。
        for j in range(14):
            phi = math.pi / 2 + 2 * math.pi * j / 14 + (math.pi / 14 if side < 0 else 0)
            c, s = math.cos(phi), math.sin(phi)
            axes = np.array([[c, 0, s], [s, 0, -c], [0, 1, 0]])
            pieces.append(placed(tread, axes, (66.8 * c, 66.8 * s, side * 9.4)))
    # URDF 的轮关节自带安装位置；这里只把轮轴对到原网格的轴向和轴心。
    c, s = math.cos(yaw), math.sin(yaw)
    basis = np.array([[-s, 0, c], [c, 0, s], [0, 1, 0]])
    offset = (-1.50040329349 * c, -1.50040329349 * s, 0)
    return [placed(part, basis, offset) for part in pieces]


def assembled_mesh(pieces):
    vertices, faces = [], []
    offset = 0
    for points, triangles in pieces:
        vertices.append(points / 1000)
        faces.append(triangles + offset)
        offset += len(points)
    return np.vstack(vertices), np.vstack(faces)


def write_base(output):
    """使用整车工具的 DAE 导出器，将底盘和四个轮子存入 output。"""
    from smooth_navigation_visuals import save_dae, unit_normals

    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    meshes = [('sentry_chassis', chassis(), (0.42, 0.46, 0.49))]
    for i, yaw in enumerate((-45, -135, 135, 45), 1):
        meshes.append((f'sentry_wheel_{i}', wheel(math.radians(yaw)), (0.08, 0.08, 0.08)))
    for name, pieces, color in meshes:
        vertices, faces = assembled_mesh(pieces)
        save_dae(output / (name + '.dae'), vertices, faces, unit_normals(vertices, faces), color)
        print(f'{name}: {len(faces)} triangles', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path, help='DAE 输出目录')
    write_base(parser.parse_args().output)
