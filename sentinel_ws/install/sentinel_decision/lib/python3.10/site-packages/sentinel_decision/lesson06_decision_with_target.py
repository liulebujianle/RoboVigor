#!/usr/bin/env python3

"""
RoboMaster 哨兵导航与决策系统
第 6 课：决策系统 + 目标点管理

这一课完成：

    血量
      ↓
    决策
      ↓
    选择任务
      ↓
    选择目标点
      ↓
    输出目标坐标

目标点不再直接写在决策逻辑里面。

而是统一使用 TargetPoint 类。

目前目标：

    BASE
    SCORE_POINT_A

注意：
目前坐标仍然是假数据。
以后拿到真实比赛地图后再修改。
"""


import rclpy

from rclpy.node import Node

from std_msgs.msg import Int32


# =====================================================
# TargetPoint
# =====================================================

class TargetPoint:

    """
    一个目标点。

    包含：

        name
        x
        y
    """

    def __init__(self, name, x, y):

        self.name = name

        self.x = x

        self.y = y


# =====================================================
# TargetManager
# =====================================================

class TargetManager:

    """
    目标管理器。

    负责保存所有比赛目标点。

    注意：

    这里暂时不是 ROS2 Node。

    它只是一个普通 Python 类。

    这样做的目的：

        决策系统
            ↓
        调用 TargetManager
            ↓
        得到目标点
    """

    def __init__(self):

        # ---------------------------------------------
        # 基地
        # ---------------------------------------------

        self.base = TargetPoint(

            "BASE",

            0.0,

            0.0
        )


        # ---------------------------------------------
        # 得分点 A
        # ---------------------------------------------

        self.score_point_a = TargetPoint(

            "SCORE_POINT_A",

            5.0,

            2.0
        )


    # ================================================
    # 获取基地
    # ================================================

    def get_base(self):

        return self.base


    # ================================================
    # 获取得分点 A
    # ================================================

    def get_score_point_a(self):

        return self.score_point_a


# =====================================================
# MissionDecision
# =====================================================

class MissionDecision(Node):

    """
    哨兵决策节点。

    输入：

        /sentinel/health

    输出：

        当前任务
        当前目标
        目标坐标
    """

    def __init__(self):

        # 初始化 ROS2 Node
        super().__init__("mission_decision_with_target")


        # ============================================
        # 当前血量
        # ============================================

        self.health = None


        # ============================================
        # 当前任务
        # ============================================

        self.mission = "UNKNOWN"


        # ============================================
        # 创建 TargetManager
        # ============================================

        self.target_manager = TargetManager()


        # ============================================
        # 当前目标
        # ============================================

        self.current_target = None


        # ============================================
        # Subscriber
        # ============================================

        self.health_subscription = self.create_subscription(

            Int32,

            "/sentinel/health",

            self.health_callback,

            10
        )


        # ============================================
        # 启动信息
        # ============================================

        self.get_logger().info(

            "Decision + Target Manager Start!"
        )


    # =================================================
    # 血量回调
    # =================================================

    def health_callback(self, msg):

        # 获取血量
        self.health = msg.data


        # 进行决策
        self.make_decision()


    # =================================================
    # 决策函数
    # =================================================

    def make_decision(self):

        # ---------------------------------------------
        # 血量高
        # ---------------------------------------------

        if self.health > 60:

            self.mission = "ATTACK_SCORE_POINT"

            # 从 TargetManager 获取目标
            self.current_target = (

                self.target_manager.get_score_point_a()
            )


        # ---------------------------------------------
        # 血量中等
        # ---------------------------------------------

        elif self.health >= 30:

            self.mission = "CAUTIOUS"

            # 暂时仍然选择得分点
            self.current_target = (

                self.target_manager.get_score_point_a()
            )


        # ---------------------------------------------
        # 血量低
        # ---------------------------------------------

        else:

            self.mission = "RETURN_BASE"

            # 从 TargetManager 获取基地
            self.current_target = (

                self.target_manager.get_base()
            )


        # 输出结果
        self.print_decision()


    # =================================================
    # 打印当前决策
    # =================================================

    def print_decision(self):

        self.get_logger().info(

            f"Health = {self.health}"
        )


        self.get_logger().info(

            f"Mission = {self.mission}"
        )


        self.get_logger().info(

            f"Target = {self.current_target.name}"
        )


        self.get_logger().info(

            f"Target Position: "

            f"X={self.current_target.x}, "

            f"Y={self.current_target.y}"
        )


# =====================================================
# main
# =====================================================

def main(args=None):

    # 初始化 ROS2
    rclpy.init(args=args)


    # 创建决策节点
    node = MissionDecision()


    # 保持运行
    rclpy.spin(node)


    # 关闭 ROS2
    rclpy.shutdown()


# =====================================================
# Python 程序入口
# =====================================================

if __name__ == "__main__":

    main()