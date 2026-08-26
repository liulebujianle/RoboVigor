#!/usr/bin/env python3

"""
RoboMaster 哨兵导航与决策系统
第 5 课：目标点管理器

这一课的目的：

把“地图目标点数据”和“决策逻辑”分开。

目前我们建立两个目标：

    BASE
        基地

    SCORE_POINT_A
        得分点 A

每个目标包含：

    名称
    X 坐标
    Y 坐标

以后拿到真实比赛地图以后，
只需要修改这里的地图数据。

注意：

目前坐标全部是假数据，
不是实际比赛地图坐标。
"""


# ROS2 Python 客户端
import rclpy

# ROS2 Node
from rclpy.node import Node


# =================================================
# TargetPoint
# =================================================

class TargetPoint:

    """
    TargetPoint 表示一个机器人目标点。

    一个目标点包含：

        name
        x
        y

    例如：

        BASE
        x = 0
        y = 0

    或：

        SCORE_POINT_A
        x = 5
        y = 2
    """

    def __init__(self, name, x, y):

        # 目标名称
        self.name = name

        # X 坐标
        self.x = x

        # Y 坐标
        self.y = y


# =================================================
# TargetManager
# =================================================

class TargetManager(Node):

    """
    TargetManager：

    负责保存机器人当前比赛地图中的目标点。

    暂时只保存：

        BASE
        SCORE_POINT_A
    """

    def __init__(self):

        # 初始化 ROS2 Node
        super().__init__("target_manager")


        # =========================================
        # 创建基地
        # =========================================

        self.base = TargetPoint(

            "BASE",

            0.0,

            0.0
        )


        # =========================================
        # 创建得分点 A
        # =========================================

        self.score_point_a = TargetPoint(

            "SCORE_POINT_A",

            5.0,

            2.0
        )


        # =========================================
        # 打印目标信息
        # =========================================

        self.get_logger().info(
            "Target Manager Start!"
        )

        self.print_target(self.base)

        self.print_target(self.score_point_a)


    # =============================================
    # 打印目标
    # =============================================

    def print_target(self, target):

        """
        打印一个目标点的信息。
        """

        self.get_logger().info(

            f"Target: {target.name}, "
            f"X={target.x}, "
            f"Y={target.y}"
        )


def main(args=None):

    # 初始化 ROS2
    rclpy.init(args=args)

    # 创建目标管理节点
    node = TargetManager()

    # 保持节点运行
    rclpy.spin(node)

    # 关闭 ROS2
    rclpy.shutdown()


if __name__ == "__main__":

    main()
