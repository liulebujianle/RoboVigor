#!/usr/bin/env python3
"""Publish the full Gazebo physics model independently of the public TF model."""
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import String


class PhysicsDescription(Node):
    """Retain the complete wheel/roller description for Gazebo spawn."""

    def __init__(self):
        super().__init__('physics_description_publisher')
        description = self.declare_parameter('robot_description', '').value
        qos = QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE,
                         durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.publisher = self.create_publisher(
            String, '/sentry_description/robot_description_physics', qos)
        self.publisher.publish(String(data=description))


def main():
    """Keep the retained physics description available to late subscribers."""
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
