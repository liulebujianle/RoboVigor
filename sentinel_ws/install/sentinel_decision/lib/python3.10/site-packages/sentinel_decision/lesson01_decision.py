#!/usr/bin/env python3

"""
RoboMaster 哨兵导航与决策系统
第 1 课：第一个 Python ROS2 决策节点

这一课暂时不进行真正的战术决策。

我们只完成：
    Python 程序
        ↓
    ROS2
        ↓
    创建一个 Node
        ↓
    成功运行

后面的课程会逐渐加入：
    血量
    比赛状态
    风险判断
    得分点
    目标选择
"""


# 导入 ROS2 Python 客户端库
#
# rclpy 可以理解成：
# “Python 与 ROS2 沟通的工具库”
import rclpy

# 从 ROS2 中导入 Node
#
# Node 就是 ROS2 系统中的一个“程序节点”
from rclpy.node import Node


# 创建我们的哨兵决策节点
#
# class 可以暂时理解成：
# “创建一种属于我们自己的对象类型”
#
# 这里我们创建一种叫：
# DecisionNode
#
# 它继承 ROS2 提供的 Node。
class DecisionNode(Node):

    # __init__ 是 Python 类的初始化函数
    #
    # 当我们创建 DecisionNode() 时，
    # 这里面的代码会自动执行。
    def __init__(self):

        # 调用父类 Node 的初始化函数
        #
        # "sentinel_decision" 是这个 ROS2 节点的名字。
        super().__init__("sentinel_decision")

        # 输出一条 ROS2 日志
        #
        # get_logger()：
        # 获取当前节点的日志工具。
        #
        # info()：
        # 输出普通的信息。
        self.get_logger().info(
            "RoboMaster Sentry Decision System Start!"
        )


# Python 程序的入口
def main(args=None):

    # 初始化 ROS2
    rclpy.init(args=args)

    # 创建我们的决策节点
    node = DecisionNode()

    # 让节点保持运行
    #
    # 如果没有这一句：
    # 程序打印完启动信息之后就会结束。
    rclpy.spin(node)

    # ROS2 关闭
    rclpy.shutdown()


# 判断：
# 当前 Python 文件是不是直接运行的？
#
# 如果我们执行：
#
# python3 lesson01_decision.py
#
# 那么 __name__ 就等于 "__main__"
#
# 此时运行 main()
if __name__ == "__main__":
    main()
