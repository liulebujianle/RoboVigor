# 控制会话、连续移动与默认启动修复 · 2026-10-29

根因证据：默认 11345 被旧裸 gzserver 占用，旧进程缺少 GAZEBO_MODEL_PATH，未加载场地；
新服务报 bind Address already in use 并退出255，客户端与 RViz 曾继续显示而没有实际车体 TF。
同时存在五个遗留 GNOME 键盘节点向同一 /teleop/* 发布，导致旧旋转/运动输入干扰新启动。
已正常关闭确认失效的旧进程。没有改用户桌面 CAD、原始 URDF 或 Autoaim。

## 实现

- Gazebo 服务退出或关闭 Gazebo 客户端窗口，停止整套 launch，包括受管理的键盘窗口。
- 每次启动用 s_ 开头的 UUID 控制会话；默认话题不会因 UUID 首字符为数字而非法。
  原始输入为 /teleop/<control_session>/cmd_vel 与 spin_mode，最终输出仍为唯一 guard 的 /cmd_vel。
- 默认前端为直接由 launch 管理的 Qt 窗口（当时是 keyboard_window.py，现已并入 keyboard_control.py），
  真实按下/松开事件；
  启动不抢走其他窗口的键盘焦点。启动 spin=false，X 幂等开启；C/空格和失焦全停。
  移动按住持续，松开减速停止平移；松开 X 不关闭已开启的小陀螺。
- 100 Hz 世界参考方向转换；实际 odom 横向纠偏（增益6 s⁻¹，附加横向速度限0.25m/s），
  制动时保持横向反馈，总速度仍受配置限制。未改变车轮接触或电机力矩物理。

## 验证

- 控制/Qt/模型/工具共24个 Python 检查通过，包括 ROS 默认会话数字首字符回归。
- 场地包8 passed、1 skipped，含服务端失败与客户端关闭的实际子进程回归；
  这些 launch 子进程检查在宿主执行，沙箱 PID/信号事件传递不可靠。
- 全部五个 ROS 包 colcon test 通过；C++ 轮子/云台检查保留，工具原有默认跳过项未伪称执行。
- 真正 Qt QTest 按下/松开事件经过实际安装的 guard 和 Gazebo：
  启动静止漂移约7.7微米；向旧 /teleop/* 发送旋转命令被忽略；/cmd_vel 只有一个发布者。
  单次按住W持续约0.756m，无初次按键重复延迟停顿；松键与C停车通过。
- 小陀螺累计7.414rad，实际云台世界航向最大偏差0.000810rad（约0.046°）。
  小陀螺中平移实测约1.001m，包含松键制动的全段最大横向偏差约0.047m；
  这不是零滑移或精确实车标定模型，仍有有限制动距离。
- lifecycle_observations.json 记录默认 GUI 出生坐标及关闭 Gazebo 后 Qt 子进程已消失。
  默认 GUI 最终留给用户的状态另附 default_observations.json 和桌面截图（验证后复制）。

metrics.json、trajectory.json 为本轮原始数据，physics_probe.py 使用 ROS_DOMAIN_ID=182、
Gazebo 11478 并写入 /tmp/robovigor-control-session-validation。轨迹测试期间 Qt 走 offscreen，
与最终默认界面实际显示验证区分。测试使用仿真时间，避免低实时率把距离误判为控制速度错误。

原验证文档中的 GNOME 终端操作属于旧版本；当前操作以工作空间 README 为准。

最终默认界面实测：出生位置 (1.249706,6.750266,0.114295)m，gyro=false，
/cmd_vel 仅一个发布者；已目视确认 Gazebo 场地与真实 CAD 机器人显示，控制窗口显示“关闭”。
default_desktop.png 是纹理完成加载后的画面，非启动加载中的截图。当前运行入口 launch PID36343。

探针附记：一次快速重启后的 Gazebo transport CLI 模型查询超时，随后的强制清理中服务端返回-11；
该次不作为启动验收。正常客户端关闭的生命周期测试清理成功，最终新启动的 GUI 日志无 ERROR/Traceback。
最终验收使用实际物理里程计、生成成功日志和实际可见 GUI，不用 transport CLI 查询超时推断模型未加载。
