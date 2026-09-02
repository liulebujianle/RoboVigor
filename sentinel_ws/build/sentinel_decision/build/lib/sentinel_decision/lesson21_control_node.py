#!/usr/bin/env python3

# ============================================================
# 第21课：模拟底盘执行节点
#
# 功能：
#   订阅 /robot_decision
#   根据决策结果，模拟底盘执行动作
#
# 当前只是“模拟执行”
# 后面会逐渐替换成：
#
#   ROS2 → cmd_vel → 底盘控制节点 → 串口 → STM32 → 麦轮
#
# ============================================================


import rclpy

# Node 是 ROS2 中所有节点的基础类
from rclpy.node import Node

# String 是我们上一课使用的消息类型
from std_msgs.msg import String


class ControlNode(Node):

    def __init__(self):

        # 创建 ROS2 节点
        super().__init__('control_node')

        # ====================================================
        # 创建订阅者
        #
        # 我们订阅：
        #
        #     /robot_decision
        #
        # 消息类型：
        #
        #     String
        #
        # 当 /robot_decision 有新的消息时，
        # ROS2 就会调用 self.decision_callback()
        # ====================================================

        self.subscription = self.create_subscription(
            String,
            '/robot_decision',
            self.decision_callback,
            10
        )

        # 启动提示
        self.get_logger().info(
            '第21课：模拟底盘控制节点已经启动'
        )

    # ========================================================
    # 决策消息回调函数
    # ========================================================

    def decision_callback(self, msg):

        # 取出收到的字符串
        decision = msg.data

        # 打印收到的决策
        self.get_logger().info(
            f'收到决策：{decision}'
        )

        # ====================================================
        # 根据决策执行不同动作
        #
        # 注意：
        # 这里现在只是打印文字。
        #
        # 后面会真正控制机器人。
        # ====================================================

        if decision == '前进':

            self.get_logger().info(
                '底盘执行：向前运动'
            )

        elif decision == '左转':

            self.get_logger().info(
                '底盘执行：向左转'
            )

        elif decision == '右转':

            self.get_logger().info(
                '底盘执行：向右转'
            )

        elif decision == '后退':

            self.get_logger().info(
                '底盘执行：向后运动'
            )

        else:

            self.get_logger().warning(
                f'未知指令：{decision}'
            )


# ============================================================
# main 函数
# ============================================================

def main(args=None):

    # 初始化 ROS2
    rclpy.init(args=args)

    # 创建控制节点
    node = ControlNode()

    # 持续运行节点
    rclpy.spin(node)

    # 节点结束后释放资源
    node.destroy_node()

    # 关闭 ROS2
    rclpy.shutdown()


# Python 程序入口
if __name__ == '__main__':
    main()