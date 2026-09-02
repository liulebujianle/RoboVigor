#!/usr/bin/env python3

"""
========================================================
RoboMaster 哨兵机器人
第20课：决策结果 ROS2 Topic 发布
========================================================

本课完成：

        /scan
          ↓
     LaserScan 数据
          ↓
      环境分析
          ↓
        决策
          ↓
   /robot_decision
          ↓
     其他 ROS2 节点

决策结果：

    前进
    左转
    右转
    后退

本课暂时使用 String。

以后我们会把它升级成真正的机器人决策消息。
========================================================
"""

# ========================================================
# 1. ROS2
# ========================================================

import rclpy

from rclpy.node import Node


# ========================================================
# 2. LaserScan
# ========================================================

from sensor_msgs.msg import LaserScan


# ========================================================
# 3. String
# ========================================================

from std_msgs.msg import String


# ========================================================
# 4. 数学库
# ========================================================

import math


# ========================================================
# 5. 安全距离
# ========================================================

SAFE_DISTANCE = 1.0


# ========================================================
# 6. 创建节点
# ========================================================

class DecisionPublisher(Node):

    def __init__(self):

        super().__init__(
            "lesson20_decision_publisher"
        )


        # =================================================
        # 订阅雷达
        # =================================================

        self.subscription = self.create_subscription(

            LaserScan,

            "/scan",

            self.scan_callback,

            10
        )


        # =================================================
        # 创建决策 Publisher
        # =================================================

        self.publisher = self.create_publisher(

            String,

            "/robot_decision",

            10
        )


        self.get_logger().info(

            "第20课：决策发布节点已经启动"
        )


    # ====================================================
    # 雷达回调
    # ====================================================

    def scan_callback(self, scan):

        # =================================================
        # 初始化四个方向
        # =================================================

        front_distance = float("inf")

        left_distance = float("inf")

        right_distance = float("inf")

        back_distance = float("inf")


        # =================================================
        # 遍历雷达
        # =================================================

        for i, distance in enumerate(scan.ranges):

            # 忽略无效数据

            if not math.isfinite(distance):

                continue


            # 忽略非法数据

            if distance < scan.range_min:

                continue

            if distance > scan.range_max:

                continue


            # 计算角度

            angle = (

                scan.angle_min

                + i * scan.angle_increment
            )

            angle_degree = math.degrees(angle)


            # =================================================
            # 前方
            # =================================================

            if -45.0 <= angle_degree <= 45.0:

                if distance < front_distance:

                    front_distance = distance


            # =================================================
            # 左方
            # =================================================

            elif 45.0 < angle_degree <= 135.0:

                if distance < left_distance:

                    left_distance = distance


            # =================================================
            # 右方
            # =================================================

            elif -135.0 <= angle_degree < -45.0:

                if distance < right_distance:

                    right_distance = distance


            # =================================================
            # 后方
            # =================================================

            else:

                if distance < back_distance:

                    back_distance = distance


        # =================================================
        # 决策
        # =================================================

        if front_distance >= SAFE_DISTANCE:

            decision = "前进"

        elif left_distance > right_distance:

            decision = "左转"

        elif right_distance > left_distance:

            decision = "右转"

        else:

            decision = "后退"


        # =================================================
        # 创建 ROS2 String 消息
        # =================================================

        msg = String()

        msg.data = decision


        # =================================================
        # 发布消息
        # =================================================

        self.publisher.publish(msg)


        # =================================================
        # 打印
        # =================================================

        self.get_logger().info(

            f"前={front_distance:.2f}m | "
            f"左={left_distance:.2f}m | "
            f"右={right_distance:.2f}m | "
            f"决策={decision}"
        )


# ========================================================
# main
# ========================================================

def main(args=None):

    rclpy.init(args=args)

    node = DecisionPublisher()

    try:

        rclpy.spin(node)

    except KeyboardInterrupt:

        pass

    node.destroy_node()

    rclpy.shutdown()


# ========================================================
# 程序入口
# ========================================================

if __name__ == "__main__":

    main()