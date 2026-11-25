#!/usr/bin/env python3
"""单独发布 Gazebo 物理模型，供仿真生成机器人。"""
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import String


class PhysicsDescription(Node):
    """通过持久化消息发布传入的物理模型描述。"""

    def __init__(self):
        super().__init__('sentry_description_publisher')
        description = self.declare_parameter('robot_description', '').value
        qos = QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE,
                         durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.publisher = self.create_publisher(
            String, '/sentry_description/robot_description_physics', qos)
        self.publisher.publish(String(data=description))


def main():
    """保持节点运行，让后启动的生成节点也能收到模型。"""
    rclpy.init()
    node = PhysicsDescription()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
