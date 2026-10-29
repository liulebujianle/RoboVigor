# sentry_motion

默认前端为 launch 直接管理的 keyboard_window.py（Qt），按下/松开控制连续移动。
启动 gyro=false；X 开启，C/空格全停；失去窗口焦点全停。独立 guard 有单调墙钟超时保护。
每次 motion.launch.py 生成独立 control_session，并给前端和 guard 配置相同输入前缀。
输出 /cmd_vel 由唯一 guard 发布；保持原有小陀螺云台参考直线平移转换。

keyboard_control.py 另保留旧终端 CLI 便于调试，但不再作为默认交互方式。
当前没有 Nav2 多源仲裁/速度平滑/碰撞监测后端。完整操作见工作空间 README。
