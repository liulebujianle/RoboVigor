# sentry_sim

Gazebo Classic 机器人仿真集成包：引用 sentry_description 模型并添加接触、全向轮力矩及云台插件。
`ros2 launch sentry_sim simulation.launch.py` 启动场地、车和 RViz。
完整键盘入口：`ros2 launch sentry_bringup sim_teleop.launch.py`。
模型网格维护在 sentry_description，键盘与保护维护在 sentry_motion。
详细配置、操作和物理限制见工作空间 README 与 docs/simulation.md。
