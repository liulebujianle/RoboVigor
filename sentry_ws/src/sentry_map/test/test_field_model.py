"""GitHub 场地材质和封闭碰撞体回归，不启动 ROS/Gazebo。"""
from pathlib import Path
import json
import unittest
import xml.etree.ElementTree as ET

MODEL = Path(__file__).resolve().parents[1] / 'models/rmul_2027'
NS = {'c': 'http://www.collada.org/2005/11/COLLADASchema'}


def signature(element):
    return (element.tag, sorted(element.attrib.items()), (element.text or '').strip(),
            [signature(child) for child in element])


class FieldModelTest(unittest.TestCase):
    def test_static_field_restores_all_github_solid_colliders(self):
        model = ET.parse(MODEL / 'model.sdf')
        self.assertEqual(model.findtext('.//static'), 'true')
        boxes = model.findall('.//collision/geometry/box/size')
        self.assertEqual(len(boxes), 29)
        reference = ET.parse(MODEL / 'source/github_model.sdf')
        self.assertEqual(signature(model.getroot()), signature(reference.getroot()))
        for box in boxes:
            self.assertTrue(all(float(v) > 0 for v in box.text.split()))

    def test_both_narrow_barriers_have_closed_volumes(self):
        model = ET.parse(MODEL / 'model.sdf')
        expected = [('c10_h0.40', (4.45, 4.825, .2)),
                    ('c11_h0.40', (7.6, 3.225, .2))]
        for name, center in expected:
            collision = next(e for e in model.findall('.//collision') if e.get('name') == name)
            size = tuple(map(float, collision.findtext('geometry/box/size').split()))
            pose = tuple(map(float, collision.findtext('pose').split()))
            self.assertEqual(size, (.2, 1.95, .4))
            self.assertEqual(pose[:3], center)
            self.assertAlmostEqual(pose[2] + size[2] / 2, .4)
            self.assertAlmostEqual(pose[2] - size[2] / 2, 0.)

    def test_exact_github_palette_and_texture_are_restored(self):
        dae = ET.parse(MODEL / 'meshes/field.dae')
        source = ET.parse(MODEL / 'source/github_field.dae')
        self.assertEqual(signature(dae.find('c:library_effects', NS)),
                         signature(source.find('c:library_effects', NS)))
        self.assertEqual(signature(dae.find('c:library_materials', NS)),
                         signature(source.find('c:library_materials', NS)))
        self.assertEqual(dae.findall('.//c:float_array', NS)[0].text,
                         source.findall('.//c:float_array', NS)[0].text)
        for image in dae.findall('.//c:image/c:init_from', NS):
            self.assertTrue((MODEL / 'meshes' / image.text).is_file())
        provenance = json.loads((MODEL / 'meshes/field_stats.json').read_text(encoding='utf-8'))
        self.assertEqual(provenance['github_commit'], 'e2ddcdb1ebbef47eaeae3490fe0c897d69083659')

    def test_classic_indices_and_material_bindings(self):
        dae = ET.parse(MODEL / 'meshes/field.dae')
        ids = [e.get('id') for e in dae.iter() if e.get('id')]
        self.assertEqual(len(ids), len(set(ids)))
        bindings = {e.get('symbol'): e for e in dae.findall('.//c:instance_material', NS)}
        for faces in dae.findall('.//c:triangles', NS):
            inputs = faces.findall('c:input', NS)
            self.assertEqual([int(e.get('offset')) for e in inputs], list(range(len(inputs))))
            indices = faces.findtext('c:p', namespaces=NS).split()
            self.assertEqual(len(indices), int(faces.get('count')) * 3 * len(inputs))
            self.assertIn(faces.get('material'), bindings)
        paper = bindings['mat_paper'].find('c:bind_vertex_input', NS)
        self.assertEqual(paper.get('semantic'), 'UVSET0')
        self.assertEqual(paper.get('input_set'), '0')

    def test_white_rim_top_faces_upward(self):
        dae = ET.parse(MODEL / 'meshes/field.dae')
        arrays = dae.findall('.//c:float_array', NS)
        positions, normals = [list(map(float, e.text.split())) for e in arrays[:2]]
        faces = next(e for e in dae.findall('.//c:triangles', NS) if e.get('material') == 'mat_white')
        stride = len(faces.findall('c:input', NS))
        indices = list(map(int, faces.findtext('c:p', namespaces=NS).split()))
        top_faces = 0
        for start in range(0, len(indices), stride * 3):
            vertices = [indices[start + i * stride] for i in range(3)]
            if all(abs(positions[index * 3 + 2] - .42) < 1e-6 for index in vertices):
                self.assertGreater(normals[indices[start + 1] * 3 + 2], .99)
                top_faces += 1
        self.assertEqual(top_faces, 48)


if __name__ == '__main__':
    unittest.main()
