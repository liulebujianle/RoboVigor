"""Check the actual environment delivered to both Gazebo processes."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


def test_server_and_client_receive_field_resources(tmp_path, monkeypatch):
    """Keep the field visible when server and GUI are separate processes."""
    # Replace the external GUI/server with tiny environment recorders so this
    # regression runs without starting a renderer or opening a ROS socket.
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
    source = Path(__file__).resolve().parents[1] / 'launch/simulation.launch.py'
    # Isolate launch's asyncio/SIGCHLD handlers from pytest's launch plugin.
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


@pytest.mark.parametrize(('closing', 'code', 'reason'), [
    ('gzserver', 255, 'Gazebo server exited'),
    ('gzclient', 0, 'Gazebo window closed'),
])
def test_server_failure_stops_the_remaining_launch(tmp_path, monkeypatch, closing, code, reason):
    """Do not leave an empty GUI running after a port conflict kills the server."""
    for executable in ('gzserver', 'gzclient'):
        body = (f'time.sleep(0.2)\nraise SystemExit({code})\n'
                if executable == closing else 'time.sleep(20)\n')
        recorder = tmp_path / executable
        recorder.write_text('#!/usr/bin/python3\nimport time\n' + body)
        recorder.chmod(0o755)
    monkeypatch.setenv('PATH', str(tmp_path) + os.pathsep + os.environ['PATH'])
    monkeypatch.setenv('ROS_LOG_DIR', str(tmp_path / 'log'))
    source = Path(__file__).resolve().parents[1] / 'launch/simulation.launch.py'
    driver = tmp_path / 'failure_probe.py'
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
    assert reason in result.stdout + result.stderr
    assert 'probe deadline' not in result.stdout + result.stderr
