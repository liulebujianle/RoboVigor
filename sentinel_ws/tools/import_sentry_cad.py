"""Import the user's assembly as a chassis with a counter-rotating yaw gimbal.

Run: python3 tools/import_sentry_cad.py /path/to/SolidWorks/folder
No source CAD file is modified. Display triangles are not exact CAD surfaces.
"""

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import struct
import sys
import xml.etree.ElementTree as ET

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))
from sldprt.assembly import read_assembly
from sldprt.blocks import read_blocks
from sentry_wheels import add_physics, recover


def sensor_hardware(mesh):
    """Remove disconnected, metre-scale view-range shells from MID-360 CAD."""
    vertices = np.asarray(mesh.vertices)
    triangles = np.asarray(mesh.triangles)
    parents = np.arange(len(vertices))

    def root(index):
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    for a, b, c in triangles:
        representative = root(a)
        parents[root(b)] = representative
        parents[root(c)] = representative
    labels = np.array([root(i) for i in range(len(vertices))])
    rejected = []
    for label in np.unique(labels):
        bounds = np.ptp(vertices[labels == label], axis=0)
        # Real MID-360 hardware shells here are under 80 mm across.
        if np.max(bounds) > 200:
            rejected.append(label)
    keep = ~np.isin(labels[triangles[:, 0]], rejected)
    return vertices, triangles[keep], int(np.count_nonzero(~keep))


def write_stl(path, vertices, triangles):
    """Write binary STL in metres, with finite outward triangle normals."""
    points = vertices[triangles]
    normals = np.cross(points[:, 1] - points[:, 0], points[:, 2] - points[:, 0])
    lengths = np.linalg.norm(normals, axis=1)
    keep = lengths > 1e-12
    points, normals, lengths = points[keep], normals[keep], lengths[keep]
    records = np.zeros(len(points), dtype=[('normal', '<f4', 3),
                                         ('vertices', '<f4', (3, 3)), ('attribute', '<u2')])
    records['normal'] = normals / lengths[:, None]
    records['vertices'] = points
    with path.open('wb') as stream:
        stream.write(b'RoboVigor native SolidWorks display mesh, metres'.ljust(80, b'\0'))
        stream.write(struct.pack('<I', len(points)))
        stream.write(records.tobytes())
    return len(points)


def main():
    """Recover all visible instances and build one shared Gazebo/RViz URDF."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    assembly = args.source / '哨兵总装.SLDASM'
    source = assembly.read_bytes()
    # Cached assembly meshes retain the exact saved component configuration.
    # Refuse partial imports rather than substituting a part's default config.
    _combined, parts, summary = read_assembly(read_blocks(source))
    if summary.no_cached_mesh or summary.nested_subassembly:
        raise RuntimeError(f'Incomplete assembly import: {summary}')
    del _combined
    root = Path(__file__).resolve().parents[1]
    package = root / 'src/sentry_description'
    roles, wheel_specs = recover([p for p in parts if not p.hidden], package / 'urdf/sentry_original.urdf')
    group_names = ['chassis', 'gimbal', *sorted(wheel_specs)]
    group_indices = {name: i for i, name in enumerate(group_names)}
    vertices, triangles, removed, groups = [], [], [], []
    offset = 0
    for component in parts:
        if component.hidden:
            continue
        v = np.asarray(component.mesh.vertices)
        t = np.asarray(component.mesh.triangles)
        if 'mid-360-asm（带范围）' in component.name:
            v, t, count = sensor_hardware(component.mesh)
            removed.append({'instance': component.name, 'range_triangles_removed': count})
        used, inverse = np.unique(t, return_inverse=True)
        v = v[used]
        t = inverse.reshape(-1, 3)
        # Native CAD: Y up. ROS: X forward, Y left, Z up. Convert mm -> m.
        v = v[:, [0, 2, 1]] * np.array([0.001, -0.001, 0.001])
        vertices.append(v)
        triangles.append(t + offset)
        group = roles.get(component.name, 'chassis' if component.name.startswith('底盘总装-') else 'gimbal')
        groups.append(np.full(len(t), group_indices[group], dtype=np.int16))
        offset += len(v)
    vertices, triangles = np.concatenate(vertices), np.concatenate(triangles)
    group_ids = np.concatenate(groups)
    upper = group_ids == 1
    if not upper.any() or upper.all():
        raise RuntimeError('Native chassis/gimbal assembly boundary was not found')
    source_bounds = [vertices.min(axis=0).tolist(), vertices.max(axis=0).tolist()]
    if max(np.ptp(vertices, axis=0)) > 0.9:
        raise RuntimeError(f'Unexpected robot bounds after range removal: {source_bounds}')
    # A 1 mm vertex grid reduces tiny screw details for interactive rendering.
    # Vertex displacement is bounded by sqrt(3)/2 mm, with no global rescaling.
    vertices, inverse = np.unique(np.round(vertices * 1000).astype(np.int32),
                                  axis=0, return_inverse=True)
    vertices = vertices * 0.001
    triangles = inverse[triangles]
    points = vertices[triangles]
    valid = np.linalg.norm(np.cross(points[:, 1] - points[:, 0],
                                    points[:, 2] - points[:, 0]), axis=1) > 1e-12
    triangles, group_ids = triangles[valid], group_ids[valid]
    upper = group_ids == 1
    written_vertices = vertices[np.unique(triangles)]
    del points
    (package / 'meshes').mkdir(exist_ok=True)
    pivot_z = 0.051  # From the user's original big_yaw_joint origin.
    chassis_count = write_stl(package / 'meshes/chassis.stl', vertices, triangles[group_ids == 0])
    gimbal_count = write_stl(package / 'meshes/gimbal.stl',
                             vertices - [0, 0, pivot_z], triangles[upper])
    count = chassis_count + gimbal_count
    wheel_counts = {}
    for name, spec in wheel_specs.items():
        wheel_counts[name] = write_stl(package / f'meshes/{name}.stl',
                                       vertices - spec['position'], triangles[group_ids == group_indices[name]])
    count += sum(wheel_counts.values())
    gimbal_vertices = vertices[triangles[upper].ravel()] - [0, 0, pivot_z]
    gimbal_center = (gimbal_vertices.min(0) + gimbal_vertices.max(0)) / 2
    dx, dy, dz = np.ptp(gimbal_vertices, axis=0)
    ixx, iyy, izz = (dy * dy + dz * dz) / 6, (dx * dx + dz * dz) / 6, (dx * dx + dy * dy) / 6
    bottom = float(written_vertices.min(axis=0)[2])
    spawn_z = round(0.003 - bottom + 0.002, 6)
    collision_z = bottom + 0.1
    urdf = f'''<?xml version="1.0"?>
<!-- Actual CAD chassis/gimbal visuals; temporary mass, inertia and box collision. -->
<robot name="robovigor_sentry">
  <link name="base_link"/>
  <link name="chassis_link">
    <visual>
      <geometry><mesh filename="package://sentry_description/meshes/chassis.stl"/></geometry>
      <material name="cad_gray"><color rgba="0.48 0.51 0.55 1"/></material>
    </visual>
    <collision>
      <origin xyz="0 0 {collision_z:.6f}"/>
      <geometry><box size="0.54 0.54 0.20"/></geometry>
    </collision>
    <inertial>
      <origin xyz="0 0 {collision_z:.6f}"/>
      <mass value="8.0"/>
      <inertia ixx="0.221066667" iyy="0.221066667" izz="0.3888" ixy="0" ixz="0" iyz="0"/>
    </inertial>
  </link>
  <joint name="chassis_fixed" type="fixed"><parent link="base_link"/><child link="chassis_link"/></joint>
  <link name="gimbal_yaw_link">
    <visual>
      <geometry><mesh filename="package://sentry_description/meshes/gimbal.stl"/></geometry>
      <material name="cad_gray"/>
    </visual>
    <inertial>
      <origin xyz="{gimbal_center[0]:.6f} {gimbal_center[1]:.6f} {gimbal_center[2]:.6f}"/>
      <mass value="2.0"/>
      <inertia ixx="{ixx:.9f}" iyy="{iyy:.9f}" izz="{izz:.9f}" ixy="0" ixz="0" iyz="0"/>
    </inertial>
  </link>
  <joint name="gimbal_yaw_joint" type="continuous">
    <parent link="chassis_link"/><child link="gimbal_yaw_link"/>
    <origin xyz="0 0 {pivot_z}"/><axis xyz="0 0 1"/>
    <limit effort="200" velocity="20"/><dynamics damping="0" friction="0"/>
  </joint>
  <gazebo reference="chassis_link"><material>Gazebo/Grey</material></gazebo>
  <gazebo reference="gimbal_yaw_link"><material>Gazebo/Grey</material></gazebo>
  <gazebo>
    <plugin name="sentry_planar_move" filename="libgazebo_ros_planar_move.so">
      <ros><namespace>/</namespace><remapping>cmd_vel:=cmd_vel</remapping><remapping>odom:=odom</remapping></ros>
      <update_rate>100.0</update_rate><publish_rate>30.0</publish_rate>
      <publish_odom>true</publish_odom><publish_odom_tf>true</publish_odom_tf>
      <odometry_frame>odom</odometry_frame><robot_base_frame>base_link</robot_base_frame>
    </plugin>
    <plugin name="sentry_gimbal_stabilizer" filename="libsentry_gimbal_stabilizer.so">
      <ros><namespace>/</namespace></ros>
    </plugin>
  </gazebo>
</robot>
'''
    robot = ET.fromstring(urdf)
    add_physics(robot, wheel_specs)
    from sentry_model_layout import write_model
    write_model(robot, package, root / 'src/sentry_sim')
    from sentry_frames import recover_frames, write_frames
    write_frames(package, recover_frames(parts, pivot_z))
    report = {'source_sha256': hashlib.sha256(source).hexdigest(),
              'assembly': asdict(summary), 'source_bounds_m': source_bounds,
              'bounds_m': [written_vertices.min(0).tolist(), written_vertices.max(0).tolist()],
              'triangles': count, 'vertex_grid_m': 0.001, 'spawn_z': spawn_z,
              'meshes': {'chassis': chassis_count, 'gimbal': gimbal_count},
              'wheel_meshes': wheel_counts,
              'wheel_geometry': wheel_specs,
              'gimbal_pivot_z': pivot_z,
              'removed_range_geometry': removed,
              'pose': 'saved CAD configuration at zero gimbal joint; articulated main yaw',
              'physics': 'torque-driven X-drive omni wheels with 112 passive roller contacts; provisional 10 kg total'}
    (package / 'urdf/sentry_cad.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)


if __name__ == '__main__':
    main()
