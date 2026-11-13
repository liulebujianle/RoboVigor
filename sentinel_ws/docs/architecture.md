# 当前结构与后续目标

本页描述源码现状（2026-11-14 核对）。FPS、Odin1 Lite接入及场地更新已写入源码；
离线检查不等于Ubuntu/ROS2/Gazebo或实体设备验收。顶层旧tree与历史记录不能直接作为功能清单。

## 启动链与职责

仿真系统入口为 `sentry_bringup/sim_teleop.launch.py`：

- `sentry_sim/simulation.launch.py` 组合场地和机器人。
- `rm_arena/simulation.launch.py` 启动Gazebo、场地Marker和RViz。
- `sentry_sim/spawn_robot.launch.py` 展开仿真Xacro、检查资源与自写插件，再生成机器人。
- `sentry_description/description.launch.py` 启动唯一原生robot_state_publisher，发布显示模型TF。
- `description_publisher.py` 发布完整物理描述到 `/sentry_description/robot_description_physics`，供spawn_entity读取。
- `sentry_motion/motion.launch.py` 默认启动 `fps_control.py`：Qt第一视角窗口与同进程速度看门狗。
  `fps:=false`切换 `keyboard_control.py`，`keyboard:=false`关闭输入节点。
- `sentry_perception/pointcloud_to_scan.launch.py` 默认把 `/lidar/points` 转换为 `/scan`。

实体雷达独立入口为 `sentry_perception/odin1_lite.launch.py`，调用单独安装的厂家
`odin_ros_driver_rev1/odin1Lite.launch.py`。它不启动Gazebo或机器人运动控制，默认关闭未标定的 `/scan`。
`odin_control.py`提供厂家建图、保存、重定位、ReMap及导出服务客户端，不实现或模拟厂家算法。

模型层负责几何、惯量、关节和参考系；仿真层追加接触、驱动与传感器；组合层负责启动装配。
Autoaim仍为独立Python工程，不参与colcon，也未连接FPS开火或自动瞄准。

## 当前模型与TF

四个轮子使用轻量圆柱几何和方向摩擦近似全向运动，没有112个独立滚子刚体。
车体与云台默认使用盒体/圆柱；原始CAD资源保留。活动关节共六个：四轮轴、云台yaw与新增pitch。
Gazebo用有限力矩驱动，四轮及云台轴TF读取实际JointState；没有底部 `wheels_link`、私有TF转发或车轮Marker。
显示转换函数仍兼容旧滚子模型，但默认模型不再实例化滚子。

底盘插件发布 `odom → base_link`；仿真发布重合的 `world → odom`。
里程计采用Gazebo世界真值，不代表实车编码器或定位精度。FPS相机在枪口前2cm，随pitch运动。
主 `lidar_link` 配置一个Odin1 Lite仿真扫描，旧 `lidar_aux_link`只保留兼容TF，无外形或扫描传感器。
`frames.yaml`保留旧CAD来源，Odin1 Lite沿用主安装位置作为仿真占位，实车需重新标定。

## 开关与保护行为

`gazebo/gui/rviz/keyboard`控制对应启动部分，`fps`选择输入模式。
`perception:=false`仅关闭点云转扫描，不关闭Xacro中已有的激光传感器。
`fps:=false`或`keyboard:=false`也不会移除30Hz枪口相机，仍保留渲染开销。

FPS点击画面捕获鼠标，WASD沿实际画面的水平朝向运动，X开启小陀螺，C/空格全停。
Esc、失焦、最小化、关窗或图像/位姿超时会停车。旧键盘模式失焦不主动停车，关窗发送全停。
输入和看门狗同进程，无UUID会话中转；超时使用单调墙钟。底盘插件另有指令超时制动。
关闭Gazebo窗口会结束整套launch；服务端异常退出的行为以启动文件与目标环境实际验收为准。

## 模块边界与后续工作

当前包含 `rm_arena`、`sentry_description`、`sentry_sim`、`sentry_motion`、`sentry_bringup`、
`sentry_perception` 六个ROS包。感知包已有点云转扫描及Odin1 Lite硬件/地图服务接入代码，
没有车体点云过滤、地形分析、Nav2或完整实车系统集成。厂家驱动和 `manifold-lc-sdk`
需要另外获取安装，`dependencies.repos`为空，不能宣称已固定或附带这些依赖。

场地保留29个近似碰撞盒；机器人云台/相机/枪管没有对应碰撞体，不能保证上部不视觉穿模。
地图资产、机器人定位融合、底盘通信、导航和比赛任务模块仍待实现。
历史验证保留在 `validation/`，旧测试数量或截图不能证明当前版本运行已验收。

使用入口见 [工作空间README](../README.md)、[仿真说明](simulation.md)、
[雷达接入](../src/sentry_perception/README.md)与[建图状态](mapping_and_localization.md)。
