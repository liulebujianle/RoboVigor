#!/usr/bin/env python3
"""向 RViz 发布安装目录中的 RMUL 场地网格。"""

from pathlib import Path

import rclpy
from ament_index_python.packages import get_package_share_directory
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, ReliabilityPolicy, QoSProfile
from visualization_msgs.msg import Marker

MESH = Path('models/rmul_2027/meshes/field.dae')


class ArenaMarker(Node):
    """用 TRANSIENT_LOCAL 保留场地消息，供后启动的 RViz 读取。"""

    def __init__(self):
        super().__init__('sentry_arena_marker')
        mesh = Path(get_package_share_directory('sentry_map')) / MESH
        if not mesh.is_file():
            raise FileNotFoundError(f'场地 DAE 文件不存在：{mesh}')
        qos = QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE,
                         durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.publisher = self.create_publisher(Marker, '/arena_marker', qos)
        self.publisher.publish(self.marker(mesh.as_uri()))
        self.get_logger().info(f'场地已发布：{mesh.as_uri()}')

    def marker(self, uri):
        """在世界坐标系原点显示米制网格，使用 DAE 自带材质。"""
        marker = Marker()
        marker.header.frame_id = 'world'
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns, marker.id = 'rmul_2027', 0
        marker.type, marker.action = Marker.MESH_RESOURCE, Marker.ADD
        marker.mesh_resource = uri
        marker.mesh_use_embedded_materials = True
        marker.pose.orientation.w = 1.0          # 其余位置/姿态默认 0 = 单位位姿
        marker.scale.x = marker.scale.y = marker.scale.z = 1.0
        marker.color.r = marker.color.g = marker.color.b = marker.color.a = 1.0
        return marker


def main(args=None):
    """保持节点运行，使 DDS 保留场地消息。"""
    rclpy.init(args=args)
    node = ArenaMarker()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
