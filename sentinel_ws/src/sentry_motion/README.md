# sentry_motion

一个进程、一个节点：`keyboard_control.py` = Qt 键盘窗口 + 同进程速度看门狗。
窗口读真实按下/松开事件，直接调用看门狗的 `receive()` / `update()`，由该节点发 `/cmd_vel`
与 `/spin_mode`。

- 启动 gyro=false；X 开启小陀螺，C/空格全停；关窗会先发一帧全停。
- 按住移动键连续走，松开即停；斜向合速度不超过 `--linear`。
- 看门狗仍做限速（1.2 m/s、4 rad/s）、0.5 s 失联归零，以及小陀螺下按云台朝向直线平移。

不再有 `/teleop/<会话>/` 中转话题，也没有独立 guard 进程（`sim_teleop` 的 `keyboard:=false`
可直接关掉整个键盘节点）。当前没有 Nav2 多源仲裁/速度平滑/碰撞监测后端。完整操作见工作空间 README。
