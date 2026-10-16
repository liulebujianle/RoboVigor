#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy
from visualization_msgs.msg import Marker


class ArenaMarker(Node):

    def __init__(self):

        super().__init__('arena_marker')

        # 创建 QoS 配置
        qos = QoSProfile(depth=1)

        # 允许后启动的 RViz2 获取最新场地模型
        qos.durability = DurabilityPolicy.TRANSIENT_LOCAL

        # 创建 Marker 发布者
        self.publisher = self.create_publisher(
            Marker,
            '/arena_marker',
            qos
        )

        # 每秒发布一次
        self.timer = self.create_timer(
            1.0,
            self.publish_arena
        )

        self.get_logger().info("RMUL 2027 场地节点已经启动")

    def publish_arena(self):

        marker = Marker()

        # 设置坐标系
        marker.header.frame_id = 'world'
        marker.header.stamp = self.get_clock().now().to_msg()

        marker.ns = 'rmul_2027'
        marker.id = 0

        # 设置 STL 模型类型
        marker.type = Marker.MESH_RESOURCE

        # 添加模型
        marker.action = Marker.ADD

        # STL 文件路径
        marker.mesh_resource = (
            'file:///home/ethan/rm_arena/meshes/rmul_2027.stl'
        )

        # 与 Gazebo 保持一致的位置
        marker.pose.position.x = -6.3
        marker.pose.position.y = -4.3
        marker.pose.position.z = 0.52

        # 绕 X 轴旋转 -90 度
        angle = math.radians(-90)

        marker.pose.orientation.x = math.sin(angle / 2)
        marker.pose.orientation.y = 0.0
        marker.pose.orientation.z = 0.0
        marker.pose.orientation.w = math.cos(angle / 2)

        # 毫米转换为米
        marker.scale.x = 0.001
        marker.scale.y = 0.001
        marker.scale.z = 0.001

        # 设置灰色
        marker.color.r = 0.8
        marker.color.g = 0.8
        marker.color.b = 0.8
        marker.color.a = 1.0

        # 发布场地模型
        self.publisher.publish(marker)


def main():

    rclpy.init()

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
