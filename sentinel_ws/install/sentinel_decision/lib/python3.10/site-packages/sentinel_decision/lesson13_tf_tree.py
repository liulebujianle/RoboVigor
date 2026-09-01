#!/usr/bin/env python3

"""
RoboMaster 哨兵导航与决策系统

第 13 课：
map → odom → base_link

本课目标：

建立一个简单的 TF 树：

    map
     ↓
    odom
     ↓
  base_link

暂时不接：

    SLAM
    激光雷达
    Nav2
    真实底盘

全部使用模拟数据。

以后：

    map → odom
        由 SLAM / 定位系统提供

    odom → base_link
        由底盘里程计提供
"""


# =====================================================
# ROS2
# =====================================================

import rclpy

from rclpy.node import Node


# =====================================================
# TF2
# =====================================================

from tf2_ros import TransformBroadcaster


# =====================================================
# Transform
# =====================================================

from geometry_msgs.msg import TransformStamped


# =====================================================
# TF2 节点
# =====================================================

class TFTreeNode(Node):

    """
    发布：

        map → odom

        odom → base_link
    """

    def __init__(self):

        super().__init__(
            "tf_tree_node"
        )


        # =================================================
        # TF Broadcaster
        # =================================================

        self.tf_broadcaster = TransformBroadcaster(

            self
        )


        # =================================================
        # Timer
        # =================================================

        self.timer = self.create_timer(

            0.1,

            self.publish_tf
        )


        self.get_logger().info(

            "TF Tree Node Start!"
        )


    # =====================================================
    # 发布 TF
    # =====================================================

    def publish_tf(self):

        # =================================================
        # map → odom
        # =================================================

        map_to_odom = TransformStamped()


        map_to_odom.header.stamp = (

            self.get_clock().now().to_msg()
        )


        # 父坐标系

        map_to_odom.header.frame_id = "map"


        # 子坐标系

        map_to_odom.child_frame_id = "odom"


        # -------------------------------------------------
        # odom 在 map 中的位置
        # -------------------------------------------------

        map_to_odom.transform.translation.x = 2.0

        map_to_odom.transform.translation.y = 1.0

        map_to_odom.transform.translation.z = 0.0


        # -------------------------------------------------
        # 无旋转
        # -------------------------------------------------

        map_to_odom.transform.rotation.x = 0.0

        map_to_odom.transform.rotation.y = 0.0

        map_to_odom.transform.rotation.z = 0.0

        map_to_odom.transform.rotation.w = 1.0


        # 发布

        self.tf_broadcaster.sendTransform(

            map_to_odom
        )


        # =================================================
        # odom → base_link
        # =================================================

        odom_to_base = TransformStamped()


        odom_to_base.header.stamp = (

            self.get_clock().now().to_msg()
        )


        # 父坐标系

        odom_to_base.header.frame_id = "odom"


        # 子坐标系

        odom_to_base.child_frame_id = "base_link"


        # -------------------------------------------------
        # base_link 在 odom 中的位置
        # -------------------------------------------------

        odom_to_base.transform.translation.x = 0.5

        odom_to_base.transform.translation.y = 0.2

        odom_to_base.transform.translation.z = 0.0


        # -------------------------------------------------
        # 无旋转
        # -------------------------------------------------

        odom_to_base.transform.rotation.x = 0.0

        odom_to_base.transform.rotation.y = 0.0

        odom_to_base.transform.rotation.z = 0.0

        odom_to_base.transform.rotation.w = 1.0


        # 发布

        self.tf_broadcaster.sendTransform(

            odom_to_base
        )


# =====================================================
# main
# =====================================================

def main(args=None):

    rclpy.init(args=args)


    node = TFTreeNode()


    rclpy.spin(node)


    rclpy.shutdown()


# =====================================================
# 程序入口
# =====================================================

if __name__ == "__main__":

    main()