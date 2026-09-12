#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist


class CmdVelMonitor(Node):

    def __init__(self):

        # 创建 ROS2 节点
        super().__init__('lesson28_cmd_vel_monitor')

        # ==========================================================
        # 订阅 /cmd_vel
        #
        # 第22课会向 /cmd_vel 发布速度指令
        # ==========================================================

        self.subscription = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )

        self.get_logger().info(
            '第28课：正在监听 /cmd_vel'
        )

    def cmd_vel_callback(self, msg):

        # ==========================================================
        # 获取机器人速度
        # ==========================================================

        vx = msg.linear.x
        vy = msg.linear.y
        wz = msg.angular.z

        # ==========================================================
        # 打印速度
        # ==========================================================

        self.get_logger().info(
            f'收到速度指令：'
            f'vx={vx:.2f} m/s, '
            f'vy={vy:.2f} m/s, '
            f'wz={wz:.2f} rad/s'
        )


def main(args=None):

    # 初始化 ROS2

    rclpy.init(args=args)

    # 创建节点

    node = CmdVelMonitor()

    try:

        # 持续等待消息

        rclpy.spin(node)

    except KeyboardInterrupt:

        pass

    finally:

        node.destroy_node()

        rclpy.shutdown()


if __name__ == '__main__':
    main()