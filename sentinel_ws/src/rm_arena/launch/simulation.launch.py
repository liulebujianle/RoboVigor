#!/usr/bin/env python3

# ROS2 Humble
# Gazebo Classic 11 + RViz2

from pathlib import Path

from launch import LaunchDescription

from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess
)

from launch.conditions import IfCondition

from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node

from ament_index_python.packages import (
    get_package_share_directory
)


def generate_launch_description():

    # 获取 ROS2 功能包安装目录
    package_dir = Path(
        get_package_share_directory('rm_arena')
    )

    # Gazebo World 文件
    world_file = (
        Path.home()
        / 'RoboVigor'
        / 'gazebo_arena'
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
            str(world_file)
        ],
        output='screen',
        condition=IfCondition(
            LaunchConfiguration('gazebo')
        )
    )

    # 发布 STL 场地
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
