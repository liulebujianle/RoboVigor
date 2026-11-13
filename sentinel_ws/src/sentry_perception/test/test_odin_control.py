"""Offline checks for service ordering, validation and failure handling."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/odin_control.py'


class OdinControlTest(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.exists(), 'Odin service client is missing')
        spec = importlib.util.spec_from_file_location('odin_control', SCRIPT)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_mapping_and_normal(self):
        self.assertEqual(self.module.build_steps('slam'), [('device_mode', 'DeviceMode', {'mode': 3})])
        self.assertEqual(self.module.build_steps('normal')[0][2], {'mode': 1})

    def test_load_requires_existing_absolute_bin_path(self):
        for value in ('relative.bin', '/definitely/missing.bin', ''):
            with self.assertRaises(ValueError):
                self.module.build_steps('relocate', value)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'map.bin'
            path.touch()
            steps = self.module.build_steps('relocate', str(path))
            self.assertEqual([s[0] for s in steps], ['device_mode', 'load_map'])
            self.assertEqual(steps[0][2], {'mode': 4})
            self.assertEqual(self.module.build_steps('remap', str(path))[0][2], {'mode': 5})

    def test_failed_mode_prevents_loading(self):
        calls = []
        def fail(service, kind, fields):
            calls.append(service)
            raise RuntimeError('device rejected mode')
        with self.assertRaises(RuntimeError):
            self.module.execute_steps([('device_mode', 'DeviceMode', {'mode': 4}),
                                       ('load_map', 'LoadMap', {'path': '/tmp/map.bin'})], fail)
        self.assertEqual(calls, ['device_mode'])

    def test_save_export_and_invalid_action(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / 'new.bin')
            self.assertEqual(self.module.build_steps('save', path)[0],
                             ('save_map', 'SaveMap', {'path': path}))
            self.assertEqual(self.module.build_steps('export', path)[0][0], 'exploy_map')
        with self.assertRaises(ValueError):
            self.module.build_steps('unknown')

    def test_rejected_and_missing_responses_fail(self):
        for response in (None, SimpleNamespace(success=False, error_code=5, message='rejected'),
                         SimpleNamespace(success=True, error_code=7, message='bad code')):
            with self.assertRaises(RuntimeError):
                self.module.checked_response(response, 'device_mode')
        self.assertEqual(self.module.checked_response(
            SimpleNamespace(success=True, error_code=0, message='OK'), 'device_mode'), 'OK')


if __name__ == '__main__':
    unittest.main()
