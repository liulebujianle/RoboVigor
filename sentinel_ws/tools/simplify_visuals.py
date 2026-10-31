"""Generate lightweight CAD display meshes; physics never uses these triangles."""
import argparse
from pathlib import Path
import struct

import numpy as np


def simplify(source, target, grid):
    """Cluster vertices on a bounded grid and remove collapsed/duplicate faces."""
    data = source.read_bytes()
    records = np.frombuffer(data, offset=84, dtype=[
        ('normal', '<f4', 3), ('vertices', '<f4', (3, 3)), ('attribute', '<u2')])
    assert len(data) == 84 + 50 * struct.unpack_from('<I', data, 80)[0]
    vertices, inverse = np.unique(
        np.round(records['vertices'].reshape(-1, 3) / grid).astype(np.int32),
        axis=0, return_inverse=True)
    triangles = inverse.reshape(-1, 3)
    vertices = vertices.astype(float) * grid
    points = vertices[triangles]
    normals = np.cross(points[:, 1] - points[:, 0], points[:, 2] - points[:, 0])
    keep = np.linalg.norm(normals, axis=1) > 1e-12
    triangles = triangles[keep]
    _, unique = np.unique(np.sort(triangles, axis=1), axis=0, return_index=True)
    points = vertices[triangles[np.sort(unique)]]
    normals = np.cross(points[:, 1] - points[:, 0], points[:, 2] - points[:, 0])
    normals /= np.linalg.norm(normals, axis=1)[:, None]
    output = np.zeros(len(points), dtype=records.dtype)
    output['vertices'], output['normal'] = points, normals
    target.write_bytes(b'RoboVigor lightweight CAD visual'.ljust(80, b'\0') +
                       struct.pack('<I', len(output)) + output.tobytes())
    return {'source_triangles': len(records), 'display_triangles': len(output),
            'grid_m': grid, 'max_vertex_displacement_m': float(np.sqrt(3) * grid / 2)}


def main():
    """Keep source CAD mesh files and write separate *_low.stl resources."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--grid', type=float, default=.004)
    args = parser.parse_args()
    if not 0 < args.grid <= .01:
        parser.error('grid must be in (0, .01] metres')
    import json
    folder = Path(__file__).resolve().parents[1] / 'src/sentry_description/meshes'
    result = {name: simplify(folder / f'{name}.stl', folder / f'{name}_low.stl', args.grid)
              for name in ('chassis', 'gimbal')}
    (folder.parent / 'config/visual_simplification.json').write_text(
        json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
