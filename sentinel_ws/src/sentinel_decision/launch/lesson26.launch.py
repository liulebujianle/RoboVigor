from launch import LaunchDescription
from launch_ros.actions import Node
import os
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    return LaunchDescription([

        # ============================================================
        # 1. map → odom
        # ============================================================
        # 作用：
        # 模拟地图坐标系 map 和 odom 坐标系之间的关系
        #
        # 当前设置：
        # x = 0
        # y = 0
        # z = 0
        # roll  = 0
        # pitch = 0
        # yaw   = 0
        #
        # 所以 map 和 odom 完全重合
        # ============================================================

        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='map_to_odom',
            arguments=[
                '0', '0', '0',
                '0', '0', '0',
                'map', 'odom'
            ]
        ),

        # ============================================================
        # 2. odom → base_link
        # ============================================================
        # 作用：
        # 模拟机器人本体 base_link 和 odom 之间的关系
        #
        # 目前为了教学，我们让它们重合
        # ============================================================

        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='odom_to_base_link',
            arguments=[
                '0', '0', '0',
                '0', '0', '0',
                'odom', 'base_link'
            ]
        ),

        # ============================================================
        # 3. base_link → laser
        # ============================================================
        # 作用：
        # 模拟 LiDAR 安装在机器人上的位置
        #
        # x = 0.2 m
        #     LiDAR 位于机器人前方 20 cm
        #
        # y = 0
        #     左右方向没有偏移
        #
        # z = 0.3 m
        #     LiDAR 位于机器人上方 30 cm
        #
        # 三个旋转角都是 0
        # ============================================================

        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_link_to_laser',
            arguments=[
                '0.2', '0', '0.3',
                '0', '0', '0',
                'base_link', 'laser'
            ]
        ),

        # ============================================================
        # 4. 启动第15课的模拟 LiDAR
        # ============================================================
        #
        # 这个程序会：
        #
        # 10 Hz 发布 /scan
        #
        # frame_id = laser
        #
        # 并且在机器人正前方 2 m 的位置模拟一个障碍物
        # ============================================================

        Node(
            package='sentinel_decision',
            executable='lesson15_scan_publisher',
            name='lesson15_scan_publisher',
            output='screen'
        ),

        # ============================================================
        # 5. 启动 RViz2
        # ============================================================
        #
        # 用 RViz2 查看：
        #
        # map
        #   ↓
        # odom
        #   ↓
        # base_link
        #   ↓
        # laser
        #
        # 以及模拟 LiDAR 的 /scan 数据
        # ============================================================

    Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',

        # 自动加载我们保存好的 RViz2 配置文件
        arguments=[
            '-d',
            os.path.join(
                get_package_share_directory('sentinel_decision'),
                'rviz',
                'lesson26.rviz'
            )
        ],

        output='screen'
    ),
    ])