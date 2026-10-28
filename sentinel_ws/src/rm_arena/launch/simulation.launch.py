#!/usr/bin/env python3

"""Launch the installed field with ROS 2 Humble, Gazebo Classic and RViz."""

import os
from pathlib import Path

from launch import LaunchDescription

from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess
)

from launch.conditions import IfCondition

from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

from ament_index_python.packages import (
    get_package_share_directory
)


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

    # 启动 Gazebo
    gazebo_process = ExecuteProcess(
        cmd=[
            'gazebo',
            '--verbose',
            # 初始化 ROS 2、发布仿真时钟，并提供模型生成服务。
            '-s', 'libgazebo_ros_init.so',
            '-s', 'libgazebo_ros_factory.so',
            str(world_file)
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
        arguments=[
            '-d',
            str(rviz_file)
        ],
        output='screen',
        condition=IfCondition(
            LaunchConfiguration('rviz')
        )
    )

    return LaunchDescription([
        gazebo_arg,
        rviz_arg,
        gazebo_process,
        marker_node,
        rviz_node
    ])
