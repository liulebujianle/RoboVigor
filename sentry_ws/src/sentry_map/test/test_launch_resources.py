"""检查 gzserver 和 gzclient 收到的资源环境变量。"""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

pytest.importorskip('launch')
pytest.importorskip('launch_ros')
pytestmark = pytest.mark.skipif(os.name != 'posix', reason='Uses POSIX executable probes')


def test_server_and_client_receive_field_resources(tmp_path, monkeypatch):
    """检查服务端和 GUI 进程都能找到场地模型。"""
    # 用记录环境变量的进程代替 Gazebo，避免启动渲染器或 ROS socket。
    for executable in ('gzserver', 'gzclient'):
        recorder = tmp_path / executable
        destination = str(tmp_path / (executable + '.json'))
        recorder.write_text(
            '#!/usr/bin/python3\nimport json, os, time\n'
            f'with open({destination!r}, "w") as stream:\n'
            '    json.dump(dict(os.environ), stream)\n'
            'time.sleep(0.2)\n'
        )
        recorder.chmod(0o755)
    monkeypatch.setenv('PATH', str(tmp_path) + os.pathsep + os.environ['PATH'])
    monkeypatch.setenv('ROS_LOG_DIR', str(tmp_path / 'log'))
    source = Path(__file__).resolve().parents[1] / 'launch/sentry_map.launch.py'
    # 在独立进程运行 launch，避免 asyncio、SIGCHLD 处理与 pytest 插件冲突。
    driver = tmp_path / 'launch_probe.py'
    driver.write_text(
        'from launch import LaunchDescription, LaunchService\n'
        'from launch.actions import IncludeLaunchDescription\n'
        'from launch.launch_description_sources import PythonLaunchDescriptionSource\n'
        'service = LaunchService()\n'
        'service.include_launch_description(LaunchDescription([\n'
        f'    IncludeLaunchDescription(PythonLaunchDescriptionSource({str(source)!r}),\n'
        "        launch_arguments={'gazebo':'true','gui':'true','rviz':'false'}.items()),\n"
        ']))\nraise SystemExit(service.run())\n'
    )
    result = subprocess.run([sys.executable, str(driver)], capture_output=True,
                            text=True, timeout=10)
    assert result.returncode == 0, result.stdout + result.stderr
    for executable in ('gzserver', 'gzclient'):
        environment = json.loads((tmp_path / (executable + '.json')).read_text())
        roots = environment.get('GAZEBO_MODEL_PATH', '').split(os.pathsep)
        assert any((Path(root) / 'rmul_2027/model.sdf').is_file() for root in roots)


def _launch_with_fake_gazebo(tmp_path, monkeypatch, failing, code):
    """用替代进程运行 launch，返回合并后的标准输出和错误输出。"""
    for executable in ('gzserver', 'gzclient'):
        body = (f'time.sleep(0.2)\nraise SystemExit({code})\n'
                if executable == failing else 'time.sleep(20)\n')
        recorder = tmp_path / executable
        recorder.write_text('#!/usr/bin/python3\nimport time\n' + body)
        recorder.chmod(0o755)
    monkeypatch.setenv('PATH', str(tmp_path) + os.pathsep + os.environ['PATH'])
    monkeypatch.setenv('ROS_LOG_DIR', str(tmp_path / 'log'))
    source = Path(__file__).resolve().parents[1] / 'launch/sentry_map.launch.py'
    driver = tmp_path / 'probe.py'
    driver.write_text(
        'from launch import LaunchDescription, LaunchService\n'
        'from launch.actions import IncludeLaunchDescription, TimerAction, EmitEvent\n'
        'from launch.events import Shutdown\n'
        'from launch.launch_description_sources import PythonLaunchDescriptionSource\n'
        'service = LaunchService()\n'
        'service.include_launch_description(LaunchDescription([\n'
        f'    IncludeLaunchDescription(PythonLaunchDescriptionSource({str(source)!r}),\n'
        "        launch_arguments={'gazebo':'true','gui':'true','rviz':'false'}.items()),\n"
        "    TimerAction(period=1.5, actions=[\n"
        "        EmitEvent(event=Shutdown(reason='probe deadline'))]),\n"
        ']))\nraise SystemExit(service.run())\n'
    )
    result = subprocess.run([sys.executable, str(driver)], capture_output=True,
                            text=True, timeout=6)
    return result.stdout + result.stderr


def test_window_close_stops_the_remaining_launch(tmp_path, monkeypatch):
    """检查关闭 Gazebo 窗口后，其他启动进程也随之退出。"""
    output = _launch_with_fake_gazebo(tmp_path, monkeypatch, 'gzclient', 0)
    assert 'Gazebo window closed' in output
    assert 'probe deadline' not in output


def test_server_failure_only_warns(tmp_path, monkeypatch):
    """检查 gzserver 退出时记录错误，RViz 和 launch 继续运行。"""
    output = _launch_with_fake_gazebo(tmp_path, monkeypatch, 'gzserver', 255)
    assert 'Gazebo server exited' in output
    # 测试计时器到期前，launch 应继续运行。
    assert 'probe deadline' in output
