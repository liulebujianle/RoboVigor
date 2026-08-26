#!/usr/bin/env python3

"""
RoboMaster 哨兵导航与决策系统
第 4 课：任务状态 + 导航目标

这一课开始让“决策系统”真正产生导航目标。

输入：
    /sentinel/health

决策：
    根据血量决定当前任务

输出：
    当前任务
    导航目标 X
    导航目标 Y

目前只考虑血量。

以后会逐渐加入：
    比赛状态
    得分点状态
    敌方威胁
    当前机器人位置
    距离
    风险
"""


import rclpy

from rclpy.node import Node

from std_msgs.msg import Int32

# ---------------------------------------------
# 注意：
#
# 这一课暂时没有使用 geometry_msgs。
#
# 我们先用两个 Int32：
#
# /sentinel/target_x
# /sentinel/target_y
#
# 表示目标坐标。
#
# 后面正式接 Nav2 时，
# 会升级成：
#
# geometry_msgs/msg/PoseStamped
#
# 那时候才是真正的 Nav2 目标点。
# ---------------------------------------------


class MissionDecision(Node):

    def __init__(self):

        # 初始化 ROS2 节点
        super().__init__("mission_decision")


        # =========================================
        # 1. 保存当前血量
        # =========================================

        self.health = None


        # =========================================
        # 2. 当前任务
        # =========================================

        # 程序刚启动的时候，
        # 还没有收到血量。
        #
        # 所以暂时设置为 UNKNOWN。
        self.mission = "UNKNOWN"


        # =========================================
        # 3. 定义基地坐标
        # =========================================

        # 注意：
        #
        # 这里的坐标只是“教学假设”。
        #
        # 不是你的真实比赛地图坐标。
        #
        # 等你以后提供真实地图，
        # 我们再修改。
        self.base_x = 0.0
        self.base_y = 0.0


        # =========================================
        # 4. 定义得分点坐标
        # =========================================

        # 同样只是教学数据。

        self.score_point_x = 5.0
        self.score_point_y = 2.0


        # =========================================
        # 5. 订阅血量
        # =========================================

        self.health_subscription = self.create_subscription(

            Int32,

            "/sentinel/health",

            self.health_callback,

            10
        )


        # =========================================
        # 6. 创建目标 X Publisher
        # =========================================

        self.target_x_publisher = self.create_publisher(

            Int32,

            "/sentinel/target_x",

            10
        )


        # =========================================
        # 7. 创建目标 Y Publisher
        # =========================================

        self.target_y_publisher = self.create_publisher(

            Int32,

            "/sentinel/target_y",

            10
        )


        # =========================================
        # 启动信息
        # =========================================

        self.get_logger().info(
            "Mission Decision System Start!"
        )


    # =============================================
    # 血量回调函数
    # =============================================

    def health_callback(self, msg):

        # 读取血量
        self.health = msg.data


        # 根据血量进行任务决策
        self.make_decision()


    # =============================================
    # 决策函数
    # =============================================

    def make_decision(self):

        # -----------------------------------------
        # 情况 1：
        # 血量大于 60
        # -----------------------------------------

        if self.health > 60:

            # 当前任务：
            # 前往得分点
            self.mission = "ATTACK_SCORE_POINT"

            # 目标：
            # 得分点
            target_x = self.score_point_x
            target_y = self.score_point_y


        # -----------------------------------------
        # 情况 2：
        # 血量 30 ~ 60
        # -----------------------------------------

        elif self.health >= 30:

            # 当前任务：
            # 谨慎行动
            self.mission = "CAUTIOUS"

            # 暂时仍然前往得分点
            #
            # 后面加入敌情以后，
            # 这里会变得更加复杂。
            target_x = self.score_point_x
            target_y = self.score_point_y


        # -----------------------------------------
        # 情况 3：
        # 血量低于 30
        # -----------------------------------------

        else:

            # 当前任务：
            # 返回基地
            self.mission = "RETURN_BASE"

            # 目标：
            # 基地
            target_x = self.base_x
            target_y = self.base_y


        # =========================================
        # 打印当前决策
        # =========================================

        self.get_logger().info(
            f"Health: {self.health}"
        )

        self.get_logger().info(
            f"Mission: {self.mission}"
        )

        self.get_logger().info(
            f"Target: X={target_x}, Y={target_y}"
        )


        # =========================================
        # 发布目标 X
        # =========================================

        x_msg = Int32()

        # 因为 Int32 只能存整数，
        # 所以这里把浮点数转换成整数。
        #
        # 这只是教学阶段。
        x_msg.data = int(target_x)

        self.target_x_publisher.publish(x_msg)


        # =========================================
        # 发布目标 Y
        # =========================================

        y_msg = Int32()

        y_msg.data = int(target_y)

        self.target_y_publisher.publish(y_msg)


def main(args=None):

    # 初始化 ROS2
    rclpy.init(args=args)

    # 创建决策节点
    node = MissionDecision()

    # 保持运行
    rclpy.spin(node)

    # 关闭 ROS2
    rclpy.shutdown()


if __name__ == "__main__":

    main()