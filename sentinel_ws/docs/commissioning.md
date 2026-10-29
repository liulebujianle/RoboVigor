# 当前验收与排错顺序

1. `colcon list --base-paths src` 应列出五个实际包，不能再列出 sentry_simulation。
2. 构建后 source install/setup.bash；`ros2 pkg prefix --share sentry_description` 应指向本工作空间安装目录。
3. `ros2 launch sentry_bringup sim_teleop.launch.py`：检查场地、唯一车、RViz 模型与键盘终端。
4. 按住 W/S、A/D，松开；X、C/空格；轮子与滚子必须转动，云台小陀螺保持世界航向。
5. 异常先看 launch 日志、description 安装网格、sim 安装 lib、robot_description、joint_states 和 /odom。
6. 功能未实现的导航/定位/通信阶段，不能用创建空目录作为验收通过。

自动检查：`python3 -m pytest -q tools/tests`；`colcon test --packages-select rm_arena sentry_description sentry_sim sentry_motion sentry_bringup`。
迁移验证结果追加到 validation/tree_migration/README.md。

启动后不按键确认 gyro=false 与出生点；点击控制窗口后再操作。
按 X 开启小陀螺，按住 W 验证世界参考直线；松开 W 只停止平移，C/空格全停。
切换窗口全停；关闭 Gazebo 窗口后检查没有残留 gzserver 或 keyboard_window.py。
