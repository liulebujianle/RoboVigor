#!/usr/bin/env python3

"""Launch the installed field with ROS 2 Humble, Gazebo Classic and RViz."""

import os
from pathlib import Path

from launch import LaunchDescription, logging

from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    GroupAction,
    EmitEvent,
    RegisterEventHandler,
)
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown

from launch.conditions import IfCondition

from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

from ament_index_python.packages import (
    get_package_share_directory
)


def stop_if_gazebo_exits(event, context):
    """Stop dependent windows and nodes when the physics server cannot run."""
    if context.is_shutdown:
        return []
    logging.get_logger('rm_arena').error(
            f'Gazebo server exited (code {event.returncode}). '
            'Check the server log and close any old Gazebo using the same port. '
            'Stopping the simulation to avoid an empty GUI and missing robot TF.'
    )
    return [EmitEvent(event=Shutdown(reason='Gazebo server exited'))]


def stop_if_window_closes(event, context):
    """Close the background server when the user closes the Gazebo window."""
    if context.is_shutdown:
        return []
    logging.get_logger('rm_arena').info('Gazebo window closed; stopping the simulation.')
    return [EmitEvent(event=Shutdown(reason='Gazebo window closed'))]


def generate_launch_description():
    """Resolve all field resources from the installed package share directory."""
    # 获取 ROS2 功能包安装目录
    package_dir = Path(
        get_package_share_directory('rm_arena')
    )

    # Gazebo World 文件
    world_file = (
        package_dir
        / 'worlds'
        / 'arena.world'
    )

    # RViz2 配置文件
    rviz_file = (
        package_dir
        / 'rviz'
        / 'arena.rviz'
    )

    # 声明参数
    gazebo_arg = DeclareLaunchArgument(
        'gazebo',
        default_value='true'
    )

    rviz_arg = DeclareLaunchArgument(
        'rviz',
        default_value='true'
    )
    gui_arg = DeclareLaunchArgument('gui', default_value='true')
    config_arg = DeclareLaunchArgument('rviz_config', default_value=str(rviz_file))
    world_arg = DeclareLaunchArgument('world', default_value=str(world_file))
    tf_arg = DeclareLaunchArgument('tf_topic', default_value='/tf')
    static_arg = DeclareLaunchArgument('tf_static_topic', default_value='/tf_static')

    # 启动 Gazebo
    gazebo_process = ExecuteProcess(
        cmd=[
            'gzserver',
            '--verbose',
            # 初始化 ROS 2、发布仿真时钟，并提供模型生成服务。
            '-s', 'libgazebo_ros_init.so',
            '-s', 'libgazebo_ros_factory.so',
            LaunchConfiguration('world')
        ],
        output='screen',
        additional_env={
            'GAZEBO_MODEL_PATH': (
                str(world_file.parents[1] / 'models')
                + os.pathsep + os.environ.get('GAZEBO_MODEL_PATH', '')
            ),
        },
        condition=IfCondition(
            LaunchConfiguration('gazebo')
        )
    )
    gazebo_client = ExecuteProcess(
        cmd=['gzclient'], output='screen',
        additional_env={
            'GAZEBO_MODEL_PATH': (
                str(world_file.parents[1] / 'models')
                + os.pathsep + os.environ.get('GAZEBO_MODEL_PATH', '')
            ),
        },
        condition=IfCondition(LaunchConfiguration('gui')),
    )

    # 发布新 STEP 场地
    marker_node = Node(
        package='rm_arena',
        executable='arena_marker',
        output='screen',
        condition=IfCondition(
            LaunchConfiguration('rviz')
        )
    )

    # 启动 RViz2
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        parameters=[{
            'use_sim_time': ParameterValue(
                LaunchConfiguration('gazebo'), value_type=bool
            ),
        }],
        remappings=[('/tf', LaunchConfiguration('tf_topic')),
                    ('/tf_static', LaunchConfiguration('tf_static_topic'))],
        arguments=[
            '-d',
            LaunchConfiguration('rviz_config')
        ],
        output='screen',
        condition=IfCondition(
            LaunchConfiguration('rviz')
        )
    )

    return LaunchDescription([
        gazebo_arg,
        rviz_arg,
        gui_arg,
        config_arg,
        world_arg,
        tf_arg,
        static_arg,
        RegisterEventHandler(OnProcessExit(
            target_action=gazebo_process, on_exit=stop_if_gazebo_exits)),
        RegisterEventHandler(OnProcessExit(
            target_action=gazebo_client, on_exit=stop_if_window_closes)),
        GroupAction(
            actions=[gazebo_process, gazebo_client],
            condition=IfCondition(LaunchConfiguration('gazebo')),
        ),
        marker_node,
        rviz_node
    ])
