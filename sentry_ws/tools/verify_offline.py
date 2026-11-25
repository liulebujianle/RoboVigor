#!/usr/bin/env python3
"""运行不依赖 ROS 环境的源码和资源检查。

需要 pytest、PyYAML、xacro 和 numpy。可从任意目录运行。
Xacro 直接查找源码包；检查中不模拟 ROS 接口。
"""
from pathlib import Path
import os
import subprocess
import sys


def main():
    # CAD 来源中有中文，Windows 下让当前进程和子进程都使用 UTF-8。
    if os.name == 'nt' and not sys.flags.utf8_mode:
        environment = dict(os.environ, PYTHONUTF8='1')
        return subprocess.call(
            [sys.executable, '-X', 'utf8', str(Path(__file__).resolve()), *sys.argv[1:]],
            env=environment)
    os.environ['PYTHONUTF8'] = '1'
    # 不加载环境中其他 pytest 插件，避免影响这组离线检查。
    os.environ.setdefault('PYTEST_DISABLE_PLUGIN_AUTOLOAD', '1')
    import pytest
    import xacro.substitution_args

    workspace = Path(__file__).resolve().parents[1]

    def find_source_package(name):
        path = workspace / 'src' / name
        if not (path / 'package.xml').is_file():
            raise ValueError('Source package not found: ' + name)
        return path.as_posix()

    # 未安装 ament 索引时，让 $(find ...) 直接定位到源码包。
    xacro.substitution_args._eval_find = find_source_package
    unavailable = {
        'src/sentry_map/test/test_copyright.py': 'ament_copyright',
        'src/sentry_map/test/test_flake8.py': 'ament_flake8',
        'src/sentry_map/test/test_pep257.py': 'ament_pep257',
        'src/sentry_map/test/test_resources.py': 'ROS package install environment',
        'src/sentry_map/test/test_launch_resources.py': 'Linux executable probes and ROS launch',
        'src/sentry_description/test/test_resources.py': 'ROS package install environment',
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
