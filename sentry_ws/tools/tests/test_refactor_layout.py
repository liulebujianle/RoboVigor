"""检查功能包、Python 源码目录和仿真插件的位置。"""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET


WORKSPACE = Path(__file__).resolve().parents[2]
PACKAGES = (
    'sentry_map', 'sentry_description', 'sentry_maps', 'sentry_sim',
    'sentry_motion', 'sentry_perception', 'sentry_localization',
    'sentry_navigation', 'sentry_decision', 'sentry_referee_bridge',
    'sentry_chassis_bridge', 'sentry_sensors', 'sentry_bringup',
)


class RefactorLayoutTest(unittest.TestCase):
    def test_requested_packages_and_build_types(self):
        actual = {path.parent.name for path in (WORKSPACE / 'src').glob('*/package.xml')}
        self.assertEqual(actual, set(PACKAGES))
        for name in PACKAGES:
            with self.subTest(package=name):
                package = WORKSPACE / 'src' / name
                manifest = ET.parse(package / 'package.xml')
                self.assertEqual(manifest.findtext('name'), name)
                build_type = 'ament_cmake' if name == 'sentry_sim' else 'ament_python'
                self.assertEqual(manifest.findtext('export/build_type'), build_type)
                if build_type == 'ament_python':
                    self.assertTrue((package / 'src' / name / '__init__.py').is_file())
                    self.assertTrue((package / 'resource' / name).is_file())

    def test_native_plugins_have_functional_source_directories(self):
        source = WORKSPACE / 'src/sentry_sim/src'
        self.assertTrue((source / 'chassis/sentry_omni_drive.cpp').is_file())
        self.assertTrue((source / 'gimbal/sentry_gimbal_stabilizer.cpp').is_file())

    def test_first_person_runtime_is_removed(self):
        for name in ('sentry_sim', 'sentry_motion', 'sentry_bringup'):
            package = WORKSPACE / 'src' / name
            for directory in ('src', 'launch', 'urdf'):
                for path in (package / directory).rglob('*'):
                    if path.is_file() and path.suffix in {'.py', '.cpp', '.xacro'}:
                        with self.subTest(path=str(path.relative_to(WORKSPACE))):
                            text = path.read_text(encoding='utf-8')
                            self.assertNotIn('/fps/', text)
                            self.assertNotIn('fps_camera.xacro', text)
                            self.assertNotIn("DeclareLaunchArgument('fps'", text)


if __name__ == '__main__':
    unittest.main()
