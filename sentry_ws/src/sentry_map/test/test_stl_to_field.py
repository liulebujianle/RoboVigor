"""STL 导入的坐标、数据校验和 Gazebo/RViz 几何一致性。"""
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest
import xml.etree.ElementTree as ET

PACKAGE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'stl_to_field', PACKAGE / 'src/sentry_map/sentry_stl_to_field.py')
converter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(converter)
NS = {'c': 'http://www.collada.org/2005/11/COLLADASchema'}


def stl_bytes(vertices):
    """构造一个三角形，源法向量置零，由导入程序重算。"""
    return bytes(80) + struct.pack('<I', 1) + struct.pack(
        '<12fH', 0, 0, 0, *vertices, 0)


class StlConverterTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source.stl'
        self.source.write_bytes(stl_bytes((300, 420, 300, 1300, 420, 300,
                                           300, 420, 1300)))

    def test_units_orientation_and_winding(self):
        triangles = converter.read_stl(self.source)
        for actual, expected in zip(triangles[0], ((12., 8., 0.), (11., 8., 0.), (12., 7., 0.))):
            for value, target in zip(actual, expected):
                self.assertAlmostEqual(value, target)
        self.assertEqual(converter.normal(triangles[0]), (0., 0., 1.))

    def test_rejects_truncated_nonfinite_and_degenerate_input(self):
        cases = [b'solid incomplete', self.source.read_bytes()[:-1],
                 stl_bytes((float('nan'), 420, 300, 1300, 420, 300, 300, 420, 1300)),
                 stl_bytes((0,) * 9)]
        for data in cases:
            with self.subTest(size=len(data)):
                self.source.write_bytes(data)
                with self.assertRaises(ValueError):
                    converter.read_stl(self.source)

    def test_generated_meshes_are_identical_and_materials_are_bound(self):
        out = self.root / 'model'
        stats = converter.convert(self.source, out)
        dae = ET.parse(out / 'meshes/field.dae')
        positions = [float(v) for v in dae.findall('.//c:float_array', NS)[0].text.split()]
        record = struct.unpack_from('<12fH', (out / 'meshes/field_collision.stl').read_bytes(), 84)
        self.assertEqual(positions, list(record[3:12]))
        symbols = {e.get('material') for e in dae.findall('.//c:triangles', NS)}
        bindings = dae.findall('.//c:instance_material', NS)
        self.assertEqual(symbols, {e.get('symbol') for e in bindings})
        for faces in dae.findall('.//c:triangles', NS):
            offsets = {e.get('semantic'): e.get('offset') for e in faces.findall('c:input', NS)}
            self.assertEqual(offsets, {'VERTEX': '0', 'NORMAL': '1'})
            indices = faces.findtext('c:p', namespaces=NS).split()
            self.assertEqual(len(indices), int(faces.get('count')) * 6)
            self.assertEqual(indices[::2], indices[1::2])
        ids = [e.get('id') for e in dae.iter() if e.get('id')]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(stats['triangles'], 1)
        self.assertEqual(stats['source_sha256'], converter.sha256(self.source))
        model = ET.parse(out / 'model.sdf')
        self.assertEqual(model.findtext('.//static'), 'true')
        self.assertEqual(model.findtext('.//collision/geometry/mesh/uri'),
                         'model://rmul_2027/meshes/field_collision.stl')


if __name__ == '__main__':
    unittest.main()
