#!/usr/bin/env python3

# ============================================================
# 第22课：将机器人决策转换成 /cmd_vel
#
# 功能：
#
#     订阅：
#         /robot_decision
#
#     接收到：
#         前进
#         左转
#         右转
#         后退
#
#     转换成：
#         geometry_msgs/msg/Twist
#
#     发布到：
#         /cmd_vel
#
# ============================================================


import rclpy

from rclpy.node import Node

# String：
# 用来接收第20课发布的机器人决策
from std_msgs.msg import String

# Twist：
# ROS2 中非常常见的机器人速度控制消息
from geometry_msgs.msg import Twist


class CmdVelPublisher(Node):

    def __init__(self):

        # 创建节点
        super().__init__('cmd_vel_publisher')

        # ====================================================
        # 创建订阅者
        #
        # 订阅：
        #     /robot_decision
        #
        # 例如：
        #
        #     data: "前进"
        #
        # ====================================================

        self.subscription = self.create_subscription(
            String,
            '/robot_decision',
            self.decision_callback,
            10
        )

        # ====================================================
        # 创建发布者
        #
        # 发布：
        #
        #     /cmd_vel
        #
        # 消息类型：
        #
        #     geometry_msgs/msg/Twist
        # ====================================================

        self.publisher = self.create_publisher(
            Twist,
            '/cmd_vel',
            10
        )

        self.get_logger().info(
            '第22课：cmd_vel控制节点已经启动'
        )

    # ========================================================
    # 收到机器人决策后执行
    # ========================================================

    def decision_callback(self, msg):

        # 取出决策字符串
        decision = msg.data

        # 创建 Twist 消息
        cmd = Twist()

        # ====================================================
        # 根据不同决策设置机器人速度
        # ====================================================

        if decision == '前进':

            # 前进速度 0.5 m/s
            cmd.linear.x = 0.5

            # 左右速度为 0
            cmd.linear.y = 0.0

            # 不旋转
            cmd.angular.z = 0.0

        elif decision == '后退':

            # 后退
            cmd.linear.x = -0.5

            cmd.linear.y = 0.0
            cmd.angular.z = 0.0

        elif decision == '左转':

            # 原地向左旋转
            cmd.linear.x = 0.0
            cmd.linear.y = 0.0

            # 正数表示逆时针旋转
            cmd.angular.z = 0.5

        elif decision == '右转':

            # 原地向右旋转
            cmd.linear.x = 0.0
            cmd.linear.y = 0.0

            # 负数表示顺时针旋转
            cmd.angular.z = -0.5

        else:

            # =================================================
            # 如果收到未知指令
            #
            # 为了安全：
            # 让机器人停止
            # =================================================

            cmd.linear.x = 0.0
            cmd.linear.y = 0.0
            cmd.angular.z = 0.0

            self.get_logger().warning(
                f'未知决策：{decision}，机器人停止'
            )

        # ====================================================
        # 发布速度指令
        # ====================================================

        self.publisher.publish(cmd)

        # 打印结果，方便我们调试
        self.get_logger().info(
            f'决策：{decision} '
            f'→ linear.x={cmd.linear.x:.2f}, '
            f'linear.y={cmd.linear.y:.2f}, '
            f'angular.z={cmd.angular.z:.2f}'
        )


def main(args=None):

    # 初始化 ROS2
    rclpy.init(args=args)

    # 创建节点
    node = CmdVelPublisher()

    # 持续运行
    rclpy.spin(node)

    # 退出时释放节点
    node.destroy_node()

    # 关闭 ROS2
    rclpy.shutdown()


if __name__ == '__main__':
    main()