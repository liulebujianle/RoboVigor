# 哨兵键盘与小陀螺验收（2026-10-29）

入口：`ros2 launch sentry_simulation sim_teleop.launch.py`。
实测使用相同入口的 gui:=false rviz:=false keyboard:=false，
另用真实伪终端运行安装后的 keyboard_control.py --keyboard 并输入按键，
未用直接发布速度消息替代键盘逻辑。
测试 ROS 域 179、Gazebo 端口 11475；测试进程均已关闭。

- W/S 分别前进约 0.378 m、后退约 0.378 m，默认指令 0.8 m/s。
- 单次 X 后无需继续按键，底盘旋转 7.032 rad，跨越完整一圈。
- 实际 Gazebo 云台 link 的世界航向最大偏差为 1.183e-6 rad；
  读取的是插件报告的真实 link WorldPose，不是目标角或仅 RViz TF。
- 重复 X 不会关闭小陀螺；旋转时 W 前进以云台世界方向为参考。
  本次前进 0.606 m、横向偏移约 0.058 m；控制存在反馈采样延迟，不是导航精度验收。
- C、空格和键盘进程被强制结束后的失联停车均通过。
- 失联后实际里程计线速度与角速度均为零，见 metrics.json。
- 场地模型 rmul_2027 与整车 robovigor_sentry 均成功查询；日志无启动或资源加载错误。
- 旧简易圆柱 URDF 已从源码与安装目录删除；默认模型为两个真实 CAD 网格，碰撞为方盒。
- Python 控制与模型资源测试 10 passed；完整 CTest 9/9 passed。
  colcon test-result 汇总 24 tests、0 errors、0 failures、3 skipped（工具链检查）。
- 独立审查后将平移参考航向改为实际 /gimbal_pose，避免拼接不同时间的里程计与关节角；
  新增回归测试先失败、修复后通过。

依旧使用理想平面运动及理想关节位置执行器，不是实车电机或轮地动力学控制器。
