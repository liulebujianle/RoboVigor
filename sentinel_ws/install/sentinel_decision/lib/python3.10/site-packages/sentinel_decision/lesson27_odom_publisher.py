#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import TransformStamped

from tf2_ros import TransformBroadcaster


class OdomPublisher(Node):

    def __init__(self):

        # ==========================================================
        # 创建 ROS2 节点
        # ==========================================================

        super().__init__('lesson27_odom_publisher')

        # ==========================================================
        # 创建 TF 广播器
        #
        # 它的作用就是：
        #
        # 不断告诉 ROS2：
        #
        # odom → base_link
        #
        # 当前机器人在哪里
        # ==========================================================

        self.tf_broadcaster = TransformBroadcaster(self)

        # ==========================================================
        # 保存机器人当前的位置
        #
        # x：前后位置
        # y：左右位置
        #
        # 这里我们让机器人沿 x 方向前进
        # ==========================================================

        self.x = 0.0
        self.y = 0.0

        # ==========================================================
        # 机器人当前朝向
        #
        # yaw = 0
        #
        # 表示机器人正朝 x 正方向
        # ==========================================================

        self.yaw = 0.0

        # ==========================================================
        # 每 0.1 秒发布一次 TF
        #
        # 也就是 10 Hz
        # ==========================================================

        self.timer = self.create_timer(
            0.1,
            self.publish_tf
        )

        self.get_logger().info(
            '第27课：动态 odom → base_link TF 开始发布'
        )

    def publish_tf(self):

        # ==========================================================
        # 模拟机器人向前移动
        #
        # 每次移动 0.05 m
        # ==========================================================

        self.x += 0.05

        # ==========================================================
        # 创建 TransformStamped
        #
        # 这是 ROS2 中描述两个坐标系关系的数据
        # ==========================================================

        transform = TransformStamped()

        # ==========================================================
        # 时间戳
        #
        # 必须告诉 ROS2：
        # 这个 TF 是什么时候产生的
        # ==========================================================

        transform.header.stamp = self.get_clock().now().to_msg()

        # ==========================================================
        # 父坐标系
        #
        # odom 是父坐标系
        # ==========================================================

        transform.header.frame_id = 'odom'

        # ==========================================================
        # 子坐标系
        #
        # base_link 是机器人本体坐标系
        # ==========================================================

        transform.child_frame_id = 'base_link'

        # ==========================================================
        # 设置机器人位置
        # ==========================================================

        transform.transform.translation.x = self.x
        transform.transform.translation.y = self.y
        transform.transform.translation.z = 0.0

        # ==========================================================
        # 设置机器人旋转
        #
        # 目前 yaw = 0
        # 所以机器人没有旋转
        #
        # 四元数：
        #
        # x = 0
        # y = 0
        # z = 0
        # w = 1
        #
        # 表示没有旋转
        # ==========================================================

        transform.transform.rotation.x = 0.0
        transform.transform.rotation.y = 0.0
        transform.transform.rotation.z = 0.0
        transform.transform.rotation.w = 1.0

        # ==========================================================
        # 发布 TF
        # ==========================================================

        self.tf_broadcaster.sendTransform(transform)

        # ==========================================================
        # 在终端打印机器人位置
        # ==========================================================

        self.get_logger().info(
            f'机器人位置：x = {self.x:.2f} m'
        )


def main(args=None):

    # 初始化 ROS2

    rclpy.init(args=args)

    # 创建节点

    node = OdomPublisher()

    try:

        # 持续运行

        rclpy.spin(node)

    except KeyboardInterrupt:

        pass

    finally:

        node.destroy_node()

        rclpy.shutdown()


if __name__ == '__main__':
    main()