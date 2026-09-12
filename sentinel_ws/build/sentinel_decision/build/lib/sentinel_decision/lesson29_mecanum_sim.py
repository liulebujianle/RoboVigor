#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist, TransformStamped
from nav_msgs.msg import Odometry

from tf2_ros import TransformBroadcaster


class MecanumSim(Node):

    def __init__(self):

        # 创建 ROS2 节点
        super().__init__('lesson29_mecanum_sim')

        # ============================================================
        # 1. 订阅 /cmd_vel
        #
        # /cmd_vel 是速度指令：
        #
        # linear.x  → 前后速度
        # linear.y  → 左右平移速度
        # angular.z → 旋转速度
        # ============================================================

        self.subscription = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )

        # ============================================================
        # 2. 发布 TF
        #
        # 发布：
        #
        # odom → base_link
        #
        # 这个 TF 表示机器人在 odom 坐标系中的位置。
        # ============================================================

        self.tf_broadcaster = TransformBroadcaster(self)

        # ============================================================
        # 3. 发布 /odom
        #
        # /odom 使用 nav_msgs/msg/Odometry
        #
        # 以后真实机器人也会有类似的数据。
        # ============================================================

        self.odom_publisher = self.create_publisher(
            Odometry,
            '/odom',
            10
        )

        # ============================================================
        # 4. 机器人当前的位置
        #
        # x：前后位置
        # y：左右位置
        # yaw：机器人朝向
        # ============================================================

        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0

        # ============================================================
        # 5. 当前速度
        # ============================================================

        self.vx = 0.0
        self.vy = 0.0
        self.wz = 0.0

        # ============================================================
        # 6. 定时器
        #
        # 20Hz
        #
        # 每 0.05 秒更新一次机器人位置。
        # ============================================================

        self.timer = self.create_timer(
            0.05,
            self.update_robot
        )

        self.get_logger().info(
            '模拟麦轮底盘启动：/cmd_vel → /odom + TF'
        )

    # ================================================================
    # 收到 /cmd_vel
    # ================================================================

    def cmd_vel_callback(self, msg):

        self.vx = msg.linear.x
        self.vy = msg.linear.y
        self.wz = msg.angular.z

    # ================================================================
    # 更新机器人位置
    # ================================================================

    def update_robot(self):

        # 时间间隔
        dt = 0.05

        # ============================================================
        # 麦轮底盘速度转换
        #
        # vx / vy 是机器人自身坐标系下的速度。
        #
        # 但是 x / y 是 odom 世界坐标系下的位置。
        #
        # 所以需要利用 yaw 进行坐标转换。
        # ============================================================

        world_vx = (
            self.vx * math.cos(self.yaw)
            - self.vy * math.sin(self.yaw)
        )

        world_vy = (
            self.vx * math.sin(self.yaw)
            + self.vy * math.cos(self.yaw)
        )

        # ============================================================
        # 积分得到新的位置
        # ============================================================

        self.x += world_vx * dt
        self.y += world_vy * dt

        # 更新朝向
        self.yaw += self.wz * dt

        # ============================================================
        # 发布 TF
        #
        # odom → base_link
        # ============================================================

        self.publish_tf()

        # ============================================================
        # 发布 /odom
        # ============================================================

        self.publish_odom()

    # ================================================================
    # 发布 TF
    # ================================================================

    def publish_tf(self):

        transform = TransformStamped()

        transform.header.stamp = self.get_clock().now().to_msg()

        transform.header.frame_id = 'odom'
        transform.child_frame_id = 'base_link'

        # 机器人位置
        transform.transform.translation.x = self.x
        transform.transform.translation.y = self.y
        transform.transform.translation.z = 0.0

        # ============================================================
        # yaw → 四元数
        #
        # ROS2 的旋转不能直接填写 yaw。
        #
        # 对于只有 yaw 的二维机器人：
        #
        # qz = sin(yaw / 2)
        # qw = cos(yaw / 2)
        # ============================================================

        transform.transform.rotation.x = 0.0
        transform.transform.rotation.y = 0.0

        transform.transform.rotation.z = math.sin(
            self.yaw / 2.0
        )

        transform.transform.rotation.w = math.cos(
            self.yaw / 2.0
        )

        # 发布 TF
        self.tf_broadcaster.sendTransform(transform)

    # ================================================================
    # 发布 /odom
    # ================================================================

    def publish_odom(self):

        odom = Odometry()

        # 时间
        odom.header.stamp = self.get_clock().now().to_msg()

        # ============================================================
        # 坐标系
        #
        # header.frame_id：
        # 机器人位置属于哪个坐标系？
        #
        # 答案：
        # odom
        # ============================================================

        odom.header.frame_id = 'odom'

        # ============================================================
        # child_frame_id：
        #
        # 这个里程计描述的是哪个机器人坐标系？
        #
        # 答案：
        # base_link
        # ============================================================

        odom.child_frame_id = 'base_link'

        # ============================================================
        # 位置
        # ============================================================

        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.position.z = 0.0

        # ============================================================
        # yaw 转四元数
        # ============================================================

        odom.pose.pose.orientation.x = 0.0
        odom.pose.pose.orientation.y = 0.0

        odom.pose.pose.orientation.z = math.sin(
            self.yaw / 2.0
        )

        odom.pose.pose.orientation.w = math.cos(
            self.yaw / 2.0
        )

        # ============================================================
        # 速度
        # ============================================================

        odom.twist.twist.linear.x = self.vx
        odom.twist.twist.linear.y = self.vy
        odom.twist.twist.angular.z = self.wz

        # 发布 /odom
        self.odom_publisher.publish(odom)


def main(args=None):

    rclpy.init(args=args)

    node = MecanumSim()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()