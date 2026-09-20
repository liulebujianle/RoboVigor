#!/usr/bin/env python3

"""
RoboMaster 哨兵导航与决策系统
第 3 课：血量 Subscriber + 基础决策

这一课实现：

    /sentinel/health
            ↓
       Subscriber
            ↓
         当前血量
            ↓
        决策函数
            ↓
    进攻 / 谨慎 / 返回基地

目前只使用“血量”一个条件。

后续会逐渐加入：
    比赛状态
    得分点
    敌方威胁
    机器人位置
    风险等级
"""


# ROS2 Python 客户端
import rclpy

# ROS2 Node
from rclpy.node import Node

# ROS2 标准整数消息
from std_msgs.msg import Int32


class DecisionSubscriber(Node):

    def __init__(self):

        # 初始化 ROS2 节点
        super().__init__("decision_subscriber")


        # ==========================================
        # 当前血量
        # ==========================================

        # 程序刚启动的时候，
        # 我们还没有收到真正的血量数据。
        #
        # 所以先设置成 None。
        self.health = None


        # ==========================================
        # 创建 Subscriber
        # ==========================================

        self.subscription = self.create_subscription(

            # 消息类型
            Int32,

            # 我们需要监听的 Topic
            "/sentinel/health",

            # 收到消息以后执行的函数
            self.health_callback,

            # QoS 队列长度
            10
        )


        # 输出启动信息
        self.get_logger().info(
            "Decision Subscriber Start!"
        )


    # ==========================================
    # 血量回调函数
    # ==========================================

    def health_callback(self, msg):

        """
        当 /sentinel/health 收到新消息时，
        ROS2 会自动调用这个函数。

        msg 就是收到的 ROS2 消息。
        """

        # 读取血量
        self.health = msg.data


        # 显示当前血量
        self.get_logger().info(
            f"Current Health: {self.health}"
        )


        # ======================================
        # 根据血量进行决策
        # ======================================

        if self.health > 60:

            decision = "ATTACK_SCORE_POINT"

        elif self.health >= 30:

            decision = "CAUTIOUS"

        else:

            decision = "RETURN_BASE"


        # 输出决策结果
        self.get_logger().info(
            f"Decision: {decision}"
        )


def main(args=None):

    # 初始化 ROS2
    rclpy.init(args=args)

    # 创建决策节点
    node = DecisionSubscriber()

    # 保持节点运行
    rclpy.spin(node)

    # 关闭 ROS2
    rclpy.shutdown()


if __name__ == "__main__":

    main()