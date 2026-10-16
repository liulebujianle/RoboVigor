#!/usr/bin/env python3

import math
from pathlib import Path

import rclpy
from rclpy.node import Node

from rclpy.qos import (
    QoSProfile,
    ReliabilityPolicy,
    DurabilityPolicy
)

from visualization_msgs.msg import Marker


class ArenaMarker(Node):

    def __init__(self):

        super().__init__('arena_marker')

        # ==============================
        # 1. 配置 QoS
        # ==============================

        qos = QoSProfile(depth=1)

        qos.reliability = ReliabilityPolicy.RELIABLE
        qos.durability = DurabilityPolicy.TRANSIENT_LOCAL

        # ==============================
        # 2. 创建 Marker 发布者
        # ==============================

        self.publisher = self.create_publisher(
            Marker,
            '/arena_marker',
            qos
        )

        # ==============================
        # 3. 获取 STL 路径
        # ==============================

        self.stl_path = (
            Path.home()
            / 'RoboVigor'
            / 'gazebo_arena'
            / 'meshes'
            / 'rmul_2027.stl'
        )

        if not self.stl_path.is_file():
            raise FileNotFoundError(
                f'STL 文件不存在：{self.stl_path}'
            )

        self.mesh_uri = self.stl_path.as_uri()

        self.get_logger().info(
            f'STL 模型路径：{self.mesh_uri}'
        )

        # ==============================
        # 4. 创建定时器
        # ==============================

        self.timer = self.create_timer(
            1.0,
            self.publish_marker
        )

        self.publish_marker()

    def publish_marker(self):

        marker = Marker()

        # 坐标系
        marker.header.frame_id = 'world'
        marker.header.stamp = self.get_clock().now().to_msg()

        marker.ns = 'rmul_2027'
        marker.id = 0

        marker.type = Marker.MESH_RESOURCE
        marker.action = Marker.ADD

        marker.mesh_resource = self.mesh_uri

        # ==============================
        # 5. 场地位置
        # ==============================

        marker.pose.position.x = -6.3
        marker.pose.position.y = -4.3
        marker.pose.position.z = 0.52

        # ==============================
        # 6. 场地旋转
        # ==============================

        angle = math.radians(-90)

        marker.pose.orientation.x = math.sin(angle / 2)
        marker.pose.orientation.y = 0.0
        marker.pose.orientation.z = 0.0
        marker.pose.orientation.w = math.cos(angle / 2)

        # ==============================
        # 7. 缩放比例
        # ==============================

        marker.scale.x = 0.001
        marker.scale.y = 0.001
        marker.scale.z = 0.001

        # ==============================
        # 8. 颜色
        # ==============================

        marker.color.r = 0.8
        marker.color.g = 0.8
        marker.color.b = 0.8
        marker.color.a = 1.0

        # 发布
        self.publisher.publish(marker)


def main(args=None):

    rclpy.init(args=args)

    node = ArenaMarker()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
