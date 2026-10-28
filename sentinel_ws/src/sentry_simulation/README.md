# RoboVigor 简易仿真与键盘控制

首次修改后构建：

```bash
source /opt/ros/humble/setup.bash
cd /home/ethan/RoboVigor/sentinel_ws
colcon build --packages-select rm_arena sentry_simulation
```

先在旧仿真终端按 Ctrl+C 退出，避免重复占用 Gazebo 端口。之后每次使用一行启动：

```bash
source /opt/ros/humble/setup.bash && source /home/ethan/RoboVigor/sentinel_ws/install/local_setup.bash && ros2 launch sentry_simulation sim_teleop.launch.py
```

启动 rm_arena 场地、Gazebo、RViz、机器人、速度看门狗和 GNOME 键盘终端。
Gazebo 和 RViz 共用一份机器人 URDF；RViz 接收 `/robot_description`，
使用 `world → odom → base_link` TF 显示机器人位置。
鼠标点击标题为 RoboVigor WASD 的终端后操作；不是点击 Gazebo 窗口。

| 按键 | 运动 |
|---|---|
| W / S | 向前 / 向后，0.2 m/s |
| A / D | 向左 / 向右横移，0.2 m/s |
| Q / E | 逆时针 / 顺时针旋转，0.5 rad/s |
| 空格 / X | 停车 |
| Ctrl+C | 在键盘终端退出控制；在主启动终端退出仿真 |

按住按键依赖系统按键重复，无新按键输入 0.3 秒后停车；初次长按可能在系统开始重复前短暂停顿。不支持组合键斜行。键盘发布 /teleop/cmd_vel，看门狗以 20 Hz 发布 /cmd_vel，失联 0.5 秒后持续发布零速度。禁止同时用其他程序向 /cmd_vel 发运动指令；当前是仿真教学控制入口，不是实车安全控制器。

默认模型半径 0.29 m，高度 0.20 m（暂定），质量 10 kg（暂定），
生成坐标 (1.25, 6.75, 0.113)。可在启动命令尾部追加 x:=... y:=... z:=...
调整位置；默认开启 RViz，rviz:=false 可关闭。全向插件不模拟麦轮打滑。
`rm_arena simulation.launch.py` 是单独的场地入口，不会生成机器人。

检查反馈：

```bash
ros2 topic echo /odom --once --field twist.twist
```

待用户验证：前后、横移、旋转、松键停车、关闭键盘终端后停车。若无法打开 GNOME 终端，保留主终端错误日志反馈。
