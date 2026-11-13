#!/usr/bin/env python3
"""Run portable source/resource tests without claiming ROS runtime coverage.

Dependencies: pytest, PyYAML, xacro, numpy. Run from any working directory.
Only Xacro package lookup is redirected to source folders; ROS APIs are not mocked.
"""
from pathlib import Path
import os
import subprocess
import sys


def main():
    # Xacro/YAML and subprocess probes read Chinese CAD provenance. Enforce the
    # same encoding for this process and its children on Windows CP936 hosts.
    if os.name == 'nt' and not sys.flags.utf8_mode:
        environment = dict(os.environ, PYTHONUTF8='1')
        return subprocess.call(
            [sys.executable, '-X', 'utf8', str(Path(__file__).resolve()), *sys.argv[1:]],
            env=environment)
    os.environ['PYTHONUTF8'] = '1'
    import pytest
    import xacro.substitution_args

    workspace = Path(__file__).resolve().parents[1]

    def find_source_package(name):
        path = workspace / 'src' / name
        if not (path / 'package.xml').is_file():
            raise ValueError('Source package not found: ' + name)
        return path.as_posix()

    # $(find ...) normally requires an installed ament index. This substitutes
    # only the resource directory, not any ROS message, launch or node behavior.
    xacro.substitution_args._eval_find = find_source_package
    unavailable = {
        'src/rm_arena/test/test_copyright.py': 'ament_copyright',
        'src/rm_arena/test/test_flake8.py': 'ament_flake8',
        'src/rm_arena/test/test_pep257.py': 'ament_pep257',
        'src/rm_arena/test/test_resources.py': 'ROS package install environment/distutils',
        'src/rm_arena/test/test_launch_resources.py': 'Linux executable probes and ROS launch',
        'src/sentry_description/test/test_display_description.py': 'ROS launch imports and Linux shebang probe',
        'src/sentry_motion/test/test_keyboard_control.py': 'generated ROS messages and rclpy',
    }
    for file, reason in unavailable.items():
        print('Excluded from portable suite: ' + file + ' (' + reason + ')')
    os.chdir(workspace)
    args = ['.', '-q', '--import-mode=importlib']
    args += ['--ignore=' + file for file in unavailable]
    args += ['--deselect=tools/tests/test_project_layout.py::test_motion_launch_starts_a_single_keyboard_node']
    return pytest.main(args)


if __name__ == '__main__':
    sys.exit(main())
