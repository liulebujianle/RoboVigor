# 当前结构与后续目标

本页描述源码现状（2026-11-01 静态核对），运行效果仍需在 Ubuntu / ROS 2 环境验收。
顶层 `最终tree.md` 同时包含旧版本快照和未来规划，不能直接当作当前功能清单。

## 启动链与职责

系统入口是 `sentry_bringup/sim_teleop.launch.py`：

- `sentry_sim/simulation.launch.py` 组合场地和机器人。
- `rm_arena/simulation.launch.py` 启动 Gazebo、场地 Marker 和 RViz。
- `sentry_sim/spawn_robot.launch.py` 展开仿真 Xacro、检查资源并生成机器人。
- `sentry_description/description.launch.py` 启动原生 robot_state_publisher，发布显示模型的 TF。
- `description_publisher.py` 单独发布完整物理描述到
  `/sentry_description/robot_description_physics`，供 Gazebo 的 spawn_entity 读取。
- `sentry_motion/motion.launch.py` 启动一个 Qt 键盘与速度看门狗进程，发布 `/cmd_vel` 和 `/spin_mode`。
- `sentry_perception/pointcloud_to_scan.launch.py` 将 `/lidar/points` 转换为 `/scan`。

模型层负责几何、惯量、关节和部件坐标系；仿真层追加材质、方向摩擦、驱动插件及模拟雷达。
组合层只负责装配参数和启动文件。Autoaim 为独立 Python 工程，不参与 colcon。

## 当前模型与 TF

当前四轮使用轻量圆柱几何和方向摩擦近似全向运动；没有 112 个独立滚子刚体。
活动关节为四个轮轴和一个云台轴，共五个。Gazebo 采用有限力矩驱动。
四个轮轴 TF 跟随实际 JointState；不存在底部 wheels_link、私有 TF 转发或独立车轮 Marker。
显示模型转换函数仍保留对旧滚子模型的兼容处理，已有测试覆盖该路径。

底盘插件发布 `odom → base_link`；仿真启动发布重合的 `world → odom`。
里程计使用 Gazebo 世界真值，不代表真实编码器或定位精度。
六个传感器/部件参考系由 `frames.yaml` 配置；CAD 名义坐标不能代替设备标定。

## 开关与进程行为

`gazebo/gui/rviz/keyboard` 控制对应启动部分。`perception:=false` 仅停用点云转扫描节点，
不关闭已包含在仿真 Xacro 中的雷达，`/lidar/points` 仍可能生成。

键盘与看门狗同进程，无 UUID 会话话题中转。松开移动键停止对应移动，C/空格全停；
窗口失去焦点不会主动停车，关窗先发送全停。底盘插件另有指令超时制动。
关闭 Gazebo 窗口会结束整套 launch；服务端异常退出仅记录错误，其他窗口继续保留。

## 后续模块

当前源码包含 rm_arena、sentry_description、sentry_sim、sentry_motion、sentry_bringup、
sentry_perception 六个包。感知层目前只有点云转扫描，未见车体点过滤或地形分析实现。
定位、地图资产包、Nav2 导航、真机 Odin 驱动装配、底盘通信和比赛任务模块尚未落地。
`dependencies.repos` 当前为空，不能据此认为已固定厂商驱动版本。

历史验证保留在 `docs/validation/`；旧版本的测试数量和截图不证明当前版本已通过运行验收。
本次精简、检查结果和待验收事项见 `code_review_2026-11-01.md`。
