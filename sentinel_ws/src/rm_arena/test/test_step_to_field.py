"""step_to_field 的命令行契约：不装 CAD 依赖也能 --help，缺依赖时报得清楚。"""

from pathlib import Path
import subprocess
import sys

import pytest

PACKAGE = Path(__file__).resolve().parents[1]


def test_help_works_without_cad_dependencies():
    """argparse 阶段不能 import cascadio/trimesh，否则 --help 都会炸。"""
    result = subprocess.run(
        [sys.executable, '-c',
         'import sys; sys.path.insert(0, %r); '
         'from rm_arena import step_to_field; '
         'sys.exit(step_to_field.main(["--help"]))' % str(PACKAGE)],
        capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    for option in ('--step', '--out', '--tol', '--texture-source'):
        assert option in result.stdout


def test_launch_file_is_installed_with_the_expected_arguments():
    """launch 里暴露的参数名是给用户的口径，别悄悄改掉。"""
    text = (PACKAGE / 'launch/step_field.launch.py').read_text(encoding='utf-8')
    for argument in ("'step'", "'convert'", "'out'", "'tol'",
                     "'gazebo'", "'gui'", "'rviz'"):
        assert argument in text
    assert 'step_to_field' in text
    assert 'OnProcessExit' in text, '转换失败必须能拦住后续启动'


def test_converter_is_registered_as_a_console_script():
    """launch 通过 lib/rm_arena/step_to_field 调用它，入口要在 setup.py 里。"""
    setup_text = (PACKAGE / 'setup.py').read_text(encoding='utf-8')
    assert 'step_to_field = rm_arena.step_to_field:main' in setup_text
