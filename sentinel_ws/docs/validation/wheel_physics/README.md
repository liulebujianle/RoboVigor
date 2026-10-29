# 轮地物理验证 · 2026-10-29

从安装后的 simulation.launch.py 加载完整 arena.world 和 robovigor_sentry，Gazebo 11 ODE。
使用独立 ROS_DOMAIN_ID=180 和 Gazebo 端口 11476，结束后关闭测试进程。
本轮无界面测试；轮子视觉通过共享 URDF、网格零位拼接检查和实际 joint_states 验证，
没有声称重新截图验证本轮 GUI。

| 检查 | 实测结果 |
| --- | --- |
| 0.8 m/s 前进 | 实际 0.796 m/s，主轮约 ±7.4 rad/s |
| 0.8 m/s 倒车 | 实际 -0.794 m/s，主轮方向反转 |
| 0.8 m/s 横移 | 实际 0.796 m/s，滚子实际转速约 58 rad/s |
| 3 rad/s 小陀螺 | 实际 2.918 rad/s，四轮同向约 9.1 rad/s |
| 小陀螺云台世界航向 | 3 秒内采样最大偏差 0.000273 rad，约 0.016° |
| 停车制动 | 1 秒后合平移速度约 0.00185 m/s、角速度 0.00142 rad/s |
| 驱动输入失联 | 停止发布命令 2.5 秒后，合平移速度约 0.000053 m/s |
| 悬空 3 m | 轮子转到约 ±3.718 rad/s，0.16 秒内车体水平位移 0.098 mm，并自由下落 |

原始测量在 air.json、ground.json、reverse.json。probe.py 是此次隔离集成探针，
需要 source ROS 和工作空间，设置上述域与端口；分别运行 `python3 probe.py --air`、
`python3 probe.py --reverse`、`python3 probe.py`。它会写入 /tmp/robovigor-wheel-validation，
测试期间不要同时启动另一台同域机器人。倒车与横移分别从初始位置运行，避免路径连贯
测试改变位置后碰到真实场地障碍。曾在连续动作探针中遇到接触障碍导致速度断言失败；
保留场地碰撞并拆开测试，没有放松空旷平面的速度要求。

构建成功；CTest 10/10 通过，包括轮地无滑移方向约束、CAD 拼接/碰撞/惯量和键盘逻辑。
colcon 汇总 31 tests、0 errors、0 failures、6 skipped；cppcheck 因本机 2.7 版工具默认跳过，
不将其算作实际静态分析已执行。额外 tools/tests/test_wheel_geometry.py 通过。
独立代码审查未发现重大物理、TF 或生命周期问题。

模型为四轮斜置全向轮，112 个被动滚子，四轮轴有限力矩驱动，无底盘直接速度赋值。
真实可视网格与简化碰撞分开：滚子使用拟合球、轮毂使用短圆柱，底盘离地。
质量、惯量、摩擦和控制参数为尚未标定的仿真假设，不能据此预测实车精确性能。
旧 validation/sentry_spin 的理想运动测量是历史记录，当前物理行为以本目录为准。


统一 sim_teleop.launch.py 的真实键盘伪终端回归也通过：W/S、重复 X、旋转中按
云台方向移动、C、空格和键盘失联停车。底盘累计转动 7.848 rad，实际云台世界航向
最大偏差 0.00272 rad（约 0.156°）；Gazebo 查询确认 rmul_2027 和 robovigor_sentry
都存在。见 keyboard_metrics.json 和 keyboard_probe.py。此测试同时覆盖看门狗与物理驱动。
