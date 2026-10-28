#!/usr/bin/env python3

"""Publish the installed RMUL field mesh for RViz."""

from pathlib import Path

from ament_index_python.packages import get_package_share_directory

import rclpy
from rclpy.node import Node

from rclpy.qos import (
    QoSProfile,
    ReliabilityPolicy,
    DurabilityPolicy
)

from visualization_msgs.msg import Marker


class ArenaMarker(Node):
    """Publish the field in world coordinates with embedded materials."""

    def __init__(self):
        """Load the installed mesh and initialize the latched publisher."""
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
        # 3. 获取 STEP DAE 路径
        # ==============================

        self.mesh_path = (
            Path(get_package_share_directory('rm_arena'))
            / 'models'
            / 'rmul_2027'
            / 'meshes'
            / 'step_textured.dae'
        )

        if not self.mesh_path.is_file():
            raise FileNotFoundError(
                f'STEP DAE 文件不存在：{self.mesh_path}'
            )

        self.mesh_uri = self.mesh_path.as_uri()

        self.get_logger().info(
            f'STEP DAE 模型路径：{self.mesh_uri}'
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
        """Publish one field mesh with metre scale and identity pose."""
        marker = Marker()

        # 坐标系
        marker.header.frame_id = 'world'
        marker.header.stamp = self.get_clock().now().to_msg()

        marker.ns = 'rmul_2027'
        marker.id = 0

        marker.type = Marker.MESH_RESOURCE
        marker.action = Marker.ADD

        marker.mesh_resource = self.mesh_uri
        marker.mesh_use_embedded_materials = True

        # ==============================
        # 5. 场地位置
        # ==============================

        marker.pose.position.x = 0.0
        marker.pose.position.y = 0.0
        marker.pose.position.z = 0.0

        # ==============================
        # 6. 场地旋转
        # ==============================

        marker.pose.orientation.x = 0.0
        marker.pose.orientation.y = 0.0
        marker.pose.orientation.z = 0.0
        marker.pose.orientation.w = 1.0

        # ==============================
        # 7. 缩放比例
        # ==============================

        marker.scale.x = 1.0
        marker.scale.y = 1.0
        marker.scale.z = 1.0

        # ==============================
        # 8. 颜色
        # ==============================

        marker.color.r = 1.0
        marker.color.g = 1.0
        marker.color.b = 1.0
        marker.color.a = 1.0

        # 发布
        self.publisher.publish(marker)


def main(args=None):
    """Run the field marker node."""
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
