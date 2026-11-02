#!/usr/bin/env python3
"""从官方 STEP 现场生成场地，然后启动 Gazebo + RViz。

    ros2 launch rm_arena step_field.launch.py step:=/path/RMUL2027_3V3_V1.0.0.stp

转换是两段式的：先跑 `step_to_field`，成功才拉起 gzserver/gzclient 和 RViz；
失败就报出缺什么依赖并结束 launch，不会留下一个空场地。
不给 step:= 或 convert:=false 时，直接用包里已有的场地启动。
"""

from pathlib import Path

from ament_index_python.packages import get_package_prefix, get_package_share_directory
from launch import LaunchDescription, logging
from launch.actions import (DeclareLaunchArgument, EmitEvent, ExecuteProcess,
                            IncludeLaunchDescription, LogInfo, OpaqueFunction,
                            RegisterEventHandler)
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

LOGGER = 'rm_arena'


def _simulation(context):
    """场地启动：world + 场地 Marker + RViz，开关全部透传。"""
    share = Path(get_package_share_directory('rm_arena'))
    return IncludeLaunchDescription(
        PythonLaunchDescriptionSource(str(share / 'launch/simulation.launch.py')),
        launch_arguments={
            'gazebo': LaunchConfiguration('gazebo'),
            'gui': LaunchConfiguration('gui'),
            'rviz': LaunchConfiguration('rviz'),
            'rviz_config': LaunchConfiguration('rviz_config'),
            'world': LaunchConfiguration('world'),
        }.items(),
    )


def _after_convert(event, context):
    """转换成功才启动 Gazebo；失败时把原因讲清楚再退出。"""
    if event.returncode != 0:
        logging.get_logger(LOGGER).error(
            f'STEP 转换失败（退出码 {event.returncode}），不启动 Gazebo。'
            '先确认依赖：python3 -m pip install --user cascadio trimesh')
        return [EmitEvent(event=Shutdown(reason='STEP 转换失败'))]
    logging.get_logger(LOGGER).info('场地已生成，开始启动 Gazebo / RViz')
    return [_simulation(context)]


def _plan(context):
    """决定这一次是“先转换再启动”还是“直接启动”。"""
    share = Path(get_package_share_directory('rm_arena'))
    step = LaunchConfiguration('step').perform(context).strip()
    convert = LaunchConfiguration('convert').perform(context).strip().lower()
    convert = convert in ('true', '1', 'yes')

    if not convert or not step:
        if convert and not step:
            logging.get_logger(LOGGER).warn(
                '没有给 step:=，直接用包里已有的场地启动（不会重新生成）')
        return [_simulation(context)]

    step_path = Path(step).expanduser()
    if not step_path.is_file():
        return [LogInfo(msg=f'[rm_arena] STEP 不存在：{step_path}，取消启动'),
                EmitEvent(event=Shutdown(reason='STEP 不存在'))]

    executable = Path(get_package_prefix('rm_arena')) / 'lib' / 'rm_arena' / 'step_to_field'
    if not executable.is_file():
        return [LogInfo(msg=f'[rm_arena] 找不到 {executable}，先 colcon build --packages-select '
                            'rm_arena'),
                EmitEvent(event=Shutdown(reason='缺少 step_to_field 可执行文件'))]

    texture = share / 'models/rmul_2027/materials/textures/official_top.png'
    process = ExecuteProcess(
        cmd=[str(executable),
             '--step', str(step_path),
             '--out', LaunchConfiguration('out'),
             '--tol', LaunchConfiguration('tol'),
             '--texture-source', str(texture)],
        output='screen')
    return [process,
            RegisterEventHandler(OnProcessExit(target_action=process,
                                               on_exit=_after_convert))]


def generate_launch_description():
    """所有开关都是 launch 参数，默认值和包里的场地一致。"""
    share = Path(get_package_share_directory('rm_arena'))
    return LaunchDescription([
        DeclareLaunchArgument(
            'step', default_value='',
            description='官方 STEP 路径；留空则直接用包里已有的场地'),
        DeclareLaunchArgument(
            'convert', default_value='true',
            description='true=每次启动都从 STEP 重新生成资产'),
        DeclareLaunchArgument(
            'out', default_value=str(share / 'models/rmul_2027'),
            description='生成目录，默认直接覆盖安装目录里的场地'),
        DeclareLaunchArgument('tol', default_value='1.0',
                              description='三角化弦差，单位 mm'),
        DeclareLaunchArgument('gazebo', default_value='true'),
        DeclareLaunchArgument('gui', default_value='true'),
        DeclareLaunchArgument('rviz', default_value='true'),
        DeclareLaunchArgument('rviz_config', default_value=str(share / 'rviz/arena.rviz')),
        DeclareLaunchArgument('world', default_value=str(share / 'worlds/arena.world')),
        OpaqueFunction(function=_plan),
    ])
