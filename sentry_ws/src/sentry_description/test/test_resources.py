"""检查 ament Python 安装内容和资源文件字节。"""
import ast
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

import setuptools  # noqa: F401; initialize the public distutils compatibility shim
from distutils.core import run_setup

PACKAGE = Path(__file__).resolve().parents[1]


def test_installed_description_contains_the_complete_fixed_resources(tmp_path, monkeypatch):
    """检查安装后包含所有固定 URDF、网格和配置资源。"""
    monkeypatch.chdir(PACKAGE)
    distribution = run_setup('setup.py', stop_after='config')
    for destination, files in distribution.data_files:
        target = tmp_path / destination
        target.mkdir(parents=True, exist_ok=True)
        for filename in files:
            shutil.copy2(filename, target / Path(filename).name)
    share = tmp_path / 'share/sentry_description'
    assert (tmp_path / 'share/ament_index/resource_index/packages/sentry_description').is_file()
    assert (share / 'launch/sentry_description.launch.py').is_file()
    for directory in ('urdf', 'meshes', 'config', 'rviz'):
        for source in (PACKAGE / directory).rglob('*'):
            if source.is_file() and '__pycache__' not in source.parts:
                installed = share / source.relative_to(PACKAGE)
                assert installed.read_bytes() == source.read_bytes(), str(source)
    assert distribution.get_version() == ET.parse(PACKAGE / 'package.xml').findtext('version')


def test_installed_entry_points_have_their_main_function(tmp_path, monkeypatch):
    """检查命令行入口指向 build_py 已安装的模块。"""
    monkeypatch.chdir(PACKAGE)
    distribution = run_setup('setup.py', stop_after='config')
    command = distribution.get_command_obj('build_py')
    command.build_lib = str(tmp_path / 'lib')
    distribution.run_command('build_py')
    commands = distribution.entry_points['console_scripts']
    expected = {
        'sentry_description_publisher': 'sentry_description.sentry_description_publisher:main',
        'sentry_pitch_preview': 'sentry_description.sentry_pitch_preview:main',
    }
    assert len(commands) == len(expected)
    installed = dict(tuple(part.strip() for part in entry.split('=', 1)) for entry in commands)
    assert installed == expected
    for target in installed.values():
        module, function = target.split(':', 1)
        path = tmp_path / 'lib' / Path(*module.split('.')).with_suffix('.py')
        assert path.is_file()
        tree = ast.parse(path.read_text(encoding='utf-8'))
        assert any(isinstance(node, ast.FunctionDef) and node.name == function for node in tree.body)
