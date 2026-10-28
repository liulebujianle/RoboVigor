# RoboVigor 导航开发记录

## 2026-10-28 rm_arena 包补齐
- models、worlds、来源说明和 README 已加入 setuptools 安装清单。
- Gazebo world 和 RViz Marker 均从 ament 的 rm_arena 安装目录解析，
  不再依赖 ~/RoboVigor/gazebo_arena 或 ROBOVIGOR_ROOT。
- 保留 Gazebo ROS 初始化、factory 插件、原有 GAZEBO_MODEL_PATH 和 RViz 开关。
- 补齐 launch、launch_ros、gazebo_ros、rviz2 运行依赖及 ament_python 构建声明；
  package.xml 与 setup.py 版本统一为 0.0.1。
- 新增安装资源闭包测试，覆盖 world → model → mesh → texture 及模型配置引用。
- 临时隔离安装和当前 sentinel_ws 的 colcon build 均成功；包目录完整 pytest
  为 4 passed、1 skipped（原有版权模板检查跳过），有工具链弃用警告。
- 标准 colcon test 的结果汇总：5 tests、0 errors、0 failures、1 skipped。
- 在 /tmp 中只 source 隔离安装，真实验证 Marker 的晚加入订阅接收、
  安装网格 URI、Gazebo /clock、/spawn_entity 服务及 rmul_2027 模型查询成功。
  运行测试使用独立 ROS 域 176 和 Gazebo 端口 11472，测试进程已退出。
- 从工作空间根目录运行 pytest 时，test_flake8/test_pep257 会扫描整个工作空间，
  因其他包的旧构建链接和已有文档格式报错；包目录测试通过，未改动其他包。
- Gazebo/RViz 图形外观仍待人工验收；本次没有推进雷达、导航或自瞄迁移。
- 启动：在 sentinel_ws 中 source /opt/ros/humble/setup.bash 和 install/setup.bash，
  然后执行 ros2 launch rm_arena simulation.launch.py。

## 已确认
- PC：Ubuntu 22.04、ROS 2 Humble、Gazebo Classic 11；车载平台计划为 Jetson Orin Nano。
- 保留现有 sentinel_ws 工作空间与 rm_arena 场地包。
- 麦克纳姆轮全向底盘，包含突出部分的整车最大直径为 580 mm。
- 导航复用成熟 C++ 组件；决策和任务管理优先 Python。
- 正式 URDF 尚未提供，先使用简化模型推进仿真；A 板协议后续确认。
- 参考项目：/home/ethan/桌面/sentry26；按需参考架构，外参、赛场坐标和硬件接口需重新核实。

## 当前模型
- src/sentry_simulation/urdf/sentry_simple.urdf：半径 0.29 m 的圆柱包络。
- 高度 0.20 m、质量 10 kg 为临时仿真参数，惯量按均匀圆柱计算。
- 用户已在 PC 验证 URDF 到 SDF 转换成功，半径和惯量正确。
- 已添加 launch/spawn_robot.launch.py：在运行中的 Gazebo 生成模型，x/y/z 可配置。
- rm_arena 的 Gazebo 启动入口已增加 ROS 初始化和 factory 插件。
- 用户已确认模型出现，且没有穿透、持续抖动或翻倒。
- 已配置 gazebo_ros_planar_move：订阅 /cmd_vel (Twist)，发布 /odom (Odometry) 和 odom -> base_link TF，反馈目标频率 30 Hz，使用仿真时间戳；运行表现待用户验证。
- /cmd_vel 分量为车体坐标 x 前、y 左、z 上，线速度 m/s，角速度 rad/s。插件是现成 C++ 实现。
- 插件反馈来自 Gazebo 世界位姿，不是真实编码器里程计；不模拟麦轮打滑，且没有指令超时停车功能，测试需显式发送零速度。
- 尚未添加雷达。插件会设置竖直速度为零，加载位置高度需要接近实际支撑面加车体半高，不能依赖初始悬空后自然下落。

## 下一步
- 用户已验证 /cmd_vel 有订阅者、/odom 输出正常，低速前进和零速度停车成功。
- 已添加 sim_teleop.launch.py 一键启动原场地、模型、键盘控制终端及独立看门狗。
- W/S 前后、A/D 横移、Q/E 旋转，空格或 X 停车；一次一个方向；默认 0.2 m/s、0.5 rad/s。
- 键盘无新输入 0.3 秒后发送零速度；看门狗输入失联 0.5 秒后输出零速度。终端依赖系统按键重复，不支持真正的 key-up 事件。
- 看门狗运行时应独占 /cmd_vel 发布；后续 Nav2 接入时需重新设计速度源选择，不能同时运行手动发布命令。
- 当前任务等待用户验证新窗口、按键运动、松键停车及关闭键盘窗口后的失联停车。尚未验证图形界面端到端效果。
- 后续依次验证全向运动、仿真里程计与 TF、雷达、地图与定位、Nav2、Python 决策任务。
- 每次只推进一个明确任务，等待用户运行反馈后继续。
