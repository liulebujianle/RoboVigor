#!/usr/bin/env python3

"""
RoboMaster 哨兵导航与决策系统
第 2 课：血量 Publisher

这一课实现：

    哨兵决策节点
          ↓
       当前血量
          ↓
    ROS2 Publisher
          ↓
    /sentinel/health
          ↓
       其他节点

目前为了学习，我们把血量固定为 100。

以后会逐渐改成真实机器人血量。
"""


# 导入 ROS2 Python 客户端
import rclpy

# 导入 ROS2 Node
from rclpy.node import Node

# 导入 ROS2 标准消息类型 Int32
#
# Int32 表示：
# 一个 32 位整数。
#
# 我们的血量暂时使用整数表示。
from std_msgs.msg import Int32


class HealthPublisher(Node):

    def __init__(self):

        # 初始化 ROS2 Node
        #
        # 节点名称：
        # health_publisher
        super().__init__("health_publisher")

        # -----------------------------------------
        # 1. 创建一个血量变量
        # -----------------------------------------

        # 当前血量
        #
        # 现在先假设机器人满血。
        self.health = 100


        # -----------------------------------------
        # 2. 创建 Publisher
        # -----------------------------------------

        self.publisher = self.create_publisher(
            Int32,                  # 消息类型
            "/sentinel/health",     # Topic 名称
            10                      # QoS 队列长度
        )


        # -----------------------------------------
        # 3. 创建 Timer
        # -----------------------------------------

        # 每 1 秒执行一次：
        #
        # self.publish_health
        #
        # 也就是说：
        #
        # 1秒
        # ↓
        # 发布血量
        #
        # 再过1秒
        # ↓
        # 再发布血量
        self.timer = self.create_timer(
            1.0,
            self.publish_health
        )


        # 输出启动信息
        self.get_logger().info(
            "Health Publisher Start!"
        )


    # -----------------------------------------
    # 发布血量的函数
    # -----------------------------------------

    def publish_health(self):

        # 创建一个 Int32 消息
        msg = Int32()

        # 把我们的血量变量放进 ROS2 消息
        msg.data = self.health

        # 发布消息
        self.publisher.publish(msg)

        # 在终端显示当前血量
        self.get_logger().info(
            f"Current Health: {self.health}"
        )


def main(args=None):

    # 初始化 ROS2
    rclpy.init(args=args)

    # 创建血量节点
    node = HealthPublisher()

    # 保持节点运行
    rclpy.spin(node)

    # 关闭 ROS2
    rclpy.shutdown()


# Python 程序入口
if __name__ == "__main__":
    main()