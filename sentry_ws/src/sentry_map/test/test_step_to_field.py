"""检查 STEP 转换命令的帮助、依赖报错和 launch 参数。"""

from pathlib import Path
import subprocess
import sys

import setuptools  # noqa: F401; initialize the public distutils compatibility shim
from distutils.core import run_setup

PACKAGE = Path(__file__).resolve().parents[1]


def test_help_works_without_cad_dependencies():
    """未安装 cascadio、trimesh 时仍可查看 --help。"""
    result = subprocess.run(
        [sys.executable, '-X', 'utf8', '-c',
         'import sys; sys.path.insert(0, %r); '
         'from sentry_map import sentry_step_to_field; '
         'sys.exit(sentry_step_to_field.main(["--help"]))' % str(PACKAGE / 'src')],
        capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    for option in ('--step', '--out', '--tol', '--texture-source'):
        assert option in result.stdout


def test_launch_file_is_installed_with_the_expected_arguments():
    """检查 launch 参数和转换失败时的退出处理。"""
    text = (PACKAGE / 'launch/sentry_step_field.launch.py').read_text(encoding='utf-8')
    for argument in ("'step'", "'convert'", "'out'", "'tol'",
                     "'gazebo'", "'gui'", "'rviz'"):
        assert argument in text
    assert 'step_to_field' in text
    assert 'OnProcessExit' in text, '转换失败必须能拦住后续启动'


def test_console_scripts_point_to_delivered_python_modules(tmp_path, monkeypatch):
    """检查 console_scripts 指向的模块已包含在 build_py 产物中。"""
    monkeypatch.chdir(PACKAGE)
    distribution = run_setup('setup.py', stop_after='config')
    command = distribution.get_command_obj('build_py')
    command.build_lib = str(tmp_path / 'lib')
    distribution.run_command('build_py')
    entries = {
        name.strip(): target.strip()
        for name, target in (entry.split('=', 1)
                             for entry in distribution.entry_points['console_scripts'])}
    assert set(entries) == {'sentry_arena_marker', 'sentry_stl_to_field',
                            'sentry_step_to_field', 'sentry_restore_github_field'}
    for target in entries.values():
        module, function = target.split(':', 1)
        assert function == 'main'
        assert (tmp_path / 'lib' / Path(*module.split('.')).with_suffix('.py')).is_file()
