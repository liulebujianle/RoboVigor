# 当前结构与后续目标

依据 /home/ethan/桌面/算法导航提示词.md 的目标树迁移；其历史环境与进度描述不覆盖本机实测。

入口链：sentry_bringup/sim_teleop.launch.py → sentry_sim/simulation.launch.py →
rm_arena/simulation.launch.py（场地、Marker、RViz）＋ sentry_sim/spawn_robot.launch.py →
sentry_description/description.launch.py 发布唯一 robot_description → Gazebo spawn_entity 读取同一话题。
另一路 bringup → sentry_motion/motion.launch.py → Qt 键盘窗口（真实按下/松开事件）及独立速度保护 → 仿真轮轴插件。

模型层仅定义车体、质量、惯量、关节及网格。sentry_sim 的 Xacro 引用模型，再加入 Gazebo 接触与驱动插件。
四轮力矩、112 被动滚子及云台力矩控制保持原实现；没有把底盘运动改成位姿动画。

目录原则：所有导航源码、工具、脚本、文档和本机数据归入 sentinel_ws；Autoaim 独立不动。
顶层旧 gazebo_arena 存入 data/legacy_gazebo_arena；运行仅使用 rm_arena 安装资源。
CAD 提取工具移入 tools，厂商 MIT 解析器保留来源和许可证。额外 C++ src/include、测试、真实多网格
和 rm_arena/models 属于已经实现功能的必要文件，保留在各自职责包内。

当前实际包为 rm_arena、sentry_description、sentry_sim、sentry_motion、sentry_bringup。
目标树中的 sentry_navigation、sentry_maps、sentry_tasks、sentry_sensors、sentry_localization、
sentry_perception、sentry_interfaces、sentry_chassis_bridge、sentry_nav_plugins、third_party 以及 deploy
尚未实现，按原文“不能一次性全部创建”“所有后期包不必提前创建”暂不建空包。
因此本次严格落实已有代码的归属与运行链，不声称未来完整树已经落地。

额外入口 sim_teleop.launch.py 是已有可验证功能的系统入口。目标中的 sim_navigation、mapping、
robot_navigation、replay 在对应后端实现后再加入，避免名称暗示具备尚未接入的导航能力。

运行保护：Gazebo 服务端异常退出会关闭整套 launch；当前唯一 guard 接收本次 UUID 会话的键盘输入，
启动时 gyro=false，Qt 子进程随 launch 结束。无焦点、松开移动键、C/空格均停止对应运动。

当前TF直接由唯一原生RSP发布：四个实际轮轴与传感器独立，滚子只作为各轮外观而非独立TF。
完整物理描述由description_publisher提供给Gazebo。没有私有TF转发或车轮Marker层。
