# RoboVigor 最终代码地图（tree + 注释）

> 状态：**2026-10-30 清理并精简后**（git 里 426 个文件有变动，未提交，随时 `git checkout` 回退）。
> 基线：ROS 2 **Humble** / Ubuntu 22.04 原生 / **Gazebo Classic 11** + 纯 RViz，`base_footprint` 贴地约定见 docs。
> 行数=文件实际行数。标记：**★** 核心 ｜ **⚙** 构建/配置 ｜ **✓** 测试 ｜ **▢** 资源 ｜ **✂** 本次精简

## 0. 这次的四个结果

1. **两个大 xacro 从 4323 行压到 422 行**：112 个滚子的 link/joint 和 112 个 Gazebo 参数块都改成
   「宏 + 一行一条数据」，展开结果与改前**逐元素相同**（模型指纹哈希未变）。
2. **删掉 70.5 MB 无引用文件**：`sentry_cad.stl`(46 MB)、重复的 `best.pt`(21.5 MB)、`build/install/log`、
   `model.rviz`、`empty.world`、两个 `camera_web.log`、两份 `.vscode`。
3. **修掉 3 处噪声**：`camera.py` 里 3 个只在注释里用到的 import、`sentry_description` 的重复依赖与无用 `rviz2`、
   `rm_arena` 包邮箱 `.com.com` 拼写；`MANIFEST.in` 指向的权重路径原本就是错的，已按 `weight/` 目录改写。
4. **没有改动物理**：links 119、joints 118、continuous 117、网格 118、球碰撞 112、`<gazebo>` 块 119 全部保持不变。
5. **Gazebo 起不来时不再踢掉整场**（追加改动）：旧 gzserver 占着 11345 导致新服务端退出时，只打一条警告，
   RViz 和键盘窗口继续留着；只有你手动关窗口才整套退出。
6. **键盘两件套合并成一个进程**（追加改动）：`keyboard_window.py` 并进 `keyboard_control.py`，
   Qt 窗口直接调用同进程看门狗，`/teleop/<会话>/cmd_vel` 这条中转话题消失；顺带删掉「点窗口外就停车」。

---

## 1. 顶层

```text
F:\RoboVigor\
├── README.md                        3 行导航，指向 sentinel_ws/README.md
├── .gitignore                       忽略 build/ install/ log/ __pycache__/ data/*
├── Autoaim/                         ── 独立 Python 工程（不经 colcon，与仿真完全解耦）
│   ├── README.md                    大恒 Galaxy SDK 安装顺序 + `autoaim_start` 用法
│   ├── setup.py                     pip install -e . → 控制台命令 autoaim_start（gxipy/opencv/flask/filterpy）
│   ├── MANIFEST.in                  ✂ 打包权重：RV_Autoaim_2026/weight/*.pt|onnx|engine（原来指向不存在的路径）
│   ├── .gitignore                   ✂ 补了 *.log，日志不再进仓库
│   └── RV_Autoaim_2026/
│       ├── __init__.py         22 行  统一导出 9 个类（re-export，不是死代码）
│       ├── start.py           258 行  ★ 入口：解析相机/兵种颜色/网页端口 → 装配模块 → 主循环
│       ├── autoaim.py         305 行  ★ 主循环：取帧 → 检测 → PnP → 卡尔曼 → 弹道 → 发布/推流
│       ├── camera.py          204 行  ★ 大恒取流线程（✂ 删掉 cv2 / PIL / numpy 三个未使用 import）
│       ├── detector.py         73 行  ★ YOLOv8 推理（onnx / TensorRT engine），出灯条与装甲板框
│       ├── pnp_solver.py       76 行  ★ solvePnP：像素框 → 相机系 3D 位姿
│       ├── kalman_tracker.py   99 行  ★ 角度卡尔曼 + 目标卡尔曼（滤波、预测）
│       ├── ballistic_solver.py 87 行  ★ 弹道补偿：初速/重力 → pitch 补偿角
│       ├── publisher.py        72 行  ★ 按兵种组帧，串口或 ROS 发 yaw/pitch
│       ├── monitor.py         205 行  ★ Flask + MJPEG 网页监视（画框、叠字）
│       ├── logger.py           22 行   极简文件日志
│       └── weight/              ▢ 9 个模型 ~220 MB（best.pt 与 best_320s.pt 字节相同，已删前者）
└── sentinel_ws/                     ── ROS 2 Humble 工作区（colcon，5 个包）
```

## 2. 工作区骨架

```text
sentinel_ws/
├── README.md                  入口命令、按键表、5 个包的职责
├── dependencies.repos         ⚙ vcstool 清单（当前无外部仓库）
├── scripts/
│   ├── build.sh               6 行  source /opt/ros/humble + colcon build --base-paths src
│   └── sim.sh                11 行  source install/setup.bash + ros2 launch sentry_bringup sim_teleop
├── data/                      本机归档（COLCON_IGNORE，不参与构建）
├── docs/                      设计文档 + validation 证据 + superpowers 历史计划（详见 §5）
├── tools/                     CAD 导入工具链（COLCON_IGNORE，不进包）
├── build/ install/ log/       ✂ 已删除；再跑一次 ./scripts/build.sh 会自动重建
└── src/                       5 个包 ↓
```

---

## 3. 五个包

### 3.1 sentry_description —— 纯模型（唯一该改模型的地方）

```text
src/sentry_description/
├── urdf/
│   ├── sentry.urdf.xacro       6 行  ★ 唯一入口：include 三个文件，本身不加内容
│   ├── chassis.xacro         241 行  ✂ ★★ 车体 + 4 轮 + 112 滚子（原 3157 行）
│   │                                 ├ 常量区     cad_mesh / roller_mass / roller_effort / roller_velocity /
│   │                                 │            roller_damping / wheel_mass / wheel_ixx / wheel_izz /
│   │                                 │            wheel_radius / wheel_length
│   │                                 ├ 宏         cad_visual（网格+灰材质）/ cad_roller（球碰撞+球惯量）/
│   │                                 │            cad_wheel（圆柱碰撞）
│   │                                 ├ 单实例     base_link → chassis_fixed → chassis_link（box 碰撞 0.30³）
│   │                                 ├ 4 行       cad_wheel 调用（位姿/轴线/转角/ixy 都在参数里）
│   │                                 └ 112 行     cad_roller 调用：序号 父轮 关节原点 轴线 质心 球半径 惯量
│   ├── gimbal.xacro           24 行  ★ chassis_link →(0,0,0.051)→ gimbal_yaw_link，continuous，effort 200
│   ├── sensors.xacro          19 行  ★ 6 个纯坐标系：lidar / lidar_aux / camera / camera_optical / gun /
│   │                                 muzzle，位姿全部 load_yaml(config/frames.yaml)，机械 CAD 名义值
│   ├── sentry_original.urdf  345 KB  ▢ 用户原始 CAD 导出，`tools/import_sentry_cad.py` 的几何参照，只在重导 CAD 时用
│   └── sentry_cad.json        70 KB  ▢ 导入报告：包围盒 / spawn_z / 装配统计（test_cad_model 读它做断言）
├── config/frames.yaml         46 行  ★ 6 个传感器的 parent/xyz/rpy + 来源与坐标约定
├── launch/description.launch.py 96 行 ★ 两份描述：
│                                      ① 给 RSP 的"显示模型"（112 滚子的 visual/collision 折算进轮子，无 roller TF）
│                                      ② 给 Gazebo 的"完整物理模型"（经 description_publisher 走 latched 话题）
├── scripts/description_publisher.py 37 行 ★ 把完整 URDF 以 TRANSIENT_LOCAL String 重发到
│                                          /sentry_description/robot_description_physics
├── meshes/                     ▢ 118 个 STL / 44 MB：chassis、gimbal、wheel_1..4、roller_001..112（✂ 删了 46 MB 的 sentry_cad.stl）
├── test/                       ✓ 3 个：网格与地面间隙、坐标系正交性、显示模型折叠逻辑
├── CMakeLists.txt             10 行  ⚙ 装 scripts→lib/；urdf/meshes/launch/config→share/（✂ 去掉已删除的 rviz）
└── package.xml                       ✂ 去掉重复的 python3-numpy 与无用的 rviz2 依赖
```

### 3.2 sentry_sim —— Gazebo Classic 外壳 + 两个 C++ 插件

```text
src/sentry_sim/
├── urdf/sentry_sim.urdf.xacro 181 行  ✂ ★★ 纯模型 + Gazebo 层（原 1166 行）：
│                                        ├ include sentry_description/urdf/sentry.urdf.xacro
│                                        ├ 宏 gazebo_grey / roller_surface
│                                        ├ 6 个零件统一 Gazebo/Grey
│                                        ├ 1 个 <gazebo> 里两个插件：云台稳定 + 四轮驱动
│                                        └ 112 行 roller_surface 调用：mu 0.9 / kp 1e5 / kd 100 /
│                                          minDepth 5e-5 / maxVel 0.1 / maxContacts 3
├── src/omni_drive.cpp        193 行  ★★ 四轮力矩驱动：/cmd_vel → 每轮目标轮速 → PI+抗饱和 → SetForce；
│                                         同时发 /odom、odom→base_link 的 TF、/joint_states（轮+滚子）
├── src/gimbal_stabilizer.cpp 121 行  ★ 云台锁世界朝向：/spin_mode → 关节力矩维持 yaw；发 /gimbal_pose
├── include/sentry_sim/omni_kinematics.hpp 15 行 ★ 全向轮公式：
│                                         ω = (ay·(vx−ωz·y) − ax·(vy+ωz·x)) / r
├── include/sentry_sim/gimbal_math.hpp     17 行 ★ hold_heading()：误差绕回 ±π 再扣掉
├── launch/simulation.launch.py 39 行   场地 + 机器人组合入口（不含键盘）
├── launch/spawn_robot.launch.py 77 行  ★ 展开 xacro → 校验每个 mesh 与 .so → package:// 改绝对 file://
│                                         → spawn_entity；再补 world→odom 静态 TF
├── config/simulation.yaml      3 行    出生点 (1.25, 6.75, 0.118) 与实体名
├── test/                       ✓ 两个 C++ 单测：轮速符号、云台绕圈收敛
├── CMakeLists.txt             63 行  ⚙ 两个 SHARED 库 + 安装 urdf/launch/config
└── package.xml                       gazebo_dev / gazebo_ros / rclcpp / tf2_ros …
```

### 3.3 sentry_motion —— 键盘窗口 + 速度看门狗（一个进程）

```text
src/sentry_motion/
├── scripts/keyboard_control.py 305 行 ✂ ★★ 一个进程、一个节点：
│                                        · VelocityGuard：限 1.2 m/s + 4 rad/s、0.5 s 失联归零、
│                                          小陀螺按 /gimbal_pose 锁世界朝向平移（横向纠偏 ≤0.25 m/s）
│                                        · KeyboardWindow：PyQt5 真实按下/松开事件、20 ms 节拍，
│                                          每帧直接调 node.receive/receive_spin/update
│                                        · 出：/cmd_vel、/spin_mode；进：/odom、/gimbal_pose
├── launch/motion.launch.py    27 行  ★ 只起这一个节点（--linear/--angular/--spin-speed）
├── config/velocity_mux.yaml    7 行  看门狗参数（timeout 0.5 / max_linear 1.2 / max_angular 4.0）
├── test/                      ✓ 183 行：限速、失联、状态机、直线纠偏、窗口事件
│                                   （含"点窗口外不再停车、关窗发一帧全停"）
└── CMakeLists.txt / package.xml  ⚙ 装 1 个脚本；依赖 rclpy + python3-pyqt5
```

### 3.4 sentry_bringup —— 只做组合，不写逻辑

```text
src/sentry_bringup/
├── launch/sim_teleop.launch.py 38 行 ★ 唯一入口（`ros2 launch sentry_bringup sim_teleop.launch.py`）：
│                                        读 sim.yaml + simulation.yaml 当默认值 → include sentry_sim/simulation
│                                        和 sentry_motion/motion；开关 gazebo/gui/rviz/keyboard + 出生点 + 三个速度
├── config/sim.yaml             7 行  gui/rviz/keyboard + linear/angular/spin 三个速度
├── rviz/navigation.rviz      245 行  默认 RViz 视角（由 bringup 传给 sim）
├── CMakeLists.txt              6 行  ⚙ 只安装 launch/config/rviz
└── package.xml                      只依赖其它四个包
```

### 3.5 rm_arena —— 场地（world + 模型 + RViz 预览）

```text
src/rm_arena/
├── launch/
│   ├── simulation.launch.py  81 行  ✂ ★ 场地总启动：gzserver/gzclient（可选）+ arena_marker + rviz2
│   │                                   （原 170 行）。事件处理：关闭 Gazebo 窗口 → 整体 Shutdown；
│   │                                   服务端自己挂掉（如旧 gzserver 占 11345）→ 只打一条警告，不再中止整场
│   ├── world.launch.py       13 行   thin wrapper：gazebo:=true rviz:=false
│   └── arena_preview.launch.py 13 行 thin wrapper：gazebo:=false rviz:=true
├── rm_arena/arena_marker.py  59 行  ✂ ★ 一条 latched MESH_RESOURCE → /arena_marker（原 155 行；
│                                       去掉 1 Hz 无意义重发，TRANSIENT_LOCAL 已保证迟到订阅者能拿到）
├── models/rmul_2027/          ▢ 场地：model.sdf + 32 个 DAE + 1 张纹理（整树安装）
├── worlds/arena.world        18 行  只 include model://，重力/物理交给 Gazebo 默认
├── rviz/arena.rviz          205 行  场地预览视角（Grid 覆盖 12×8 m，test_resources 会校验）
├── test/                      ✓ 5 个文件：lint 模板 3 个 + 资源自包含 + launch（进程环境 / 关窗中止 /
│                                   服务端挂只警告）
├── setup.py                  36 行  ✂ ⚙ ament_python 打包（原 80 行）：launch/rviz + models/worlds/docs 整树
└── package.xml                       ✂ 修正 maintainer 邮箱 `.com.com`
```

---

## 4. tools 与 docs（都不进 colcon）

```text
tools/                          有 COLCON_IGNORE，纯开发期脚本
├── import_sentry_cad.py  219 行 ★ CAD 一键导入：SLDASM 缓存网格 → 分底盘/云台/4 轮 →
│                                 写 chassis/gimbal/sensors.xacro + 118 个 STL
├── sentry_wheels.py      162 行 ★ 滚子识别：匹配原始轴线、生成球碰撞与惯量
├── sentry_frames.py       79 行 ★ 从 CAD 实例反算 6 个传感器坐标系 → frames.yaml
├── sentry_model_layout.py 53 行 ★ 把"完整模型"拆成 description（纯）+ sim（Gazebo）两个文件
├── tests/                  ✓ 3 个：CAD 目录解析、包边界与模型指纹、轮轴手性
└── vendor/sldprt/          ▢ MIT 的 SolidWorks 解析器（保留 LICENSE / NOTICE）

docs/
├── project_tree.md            目录现状（✂ 本次已同步：118 网格、删掉 model.rviz/empty.world、补清理记录）
├── target_tree.md             目标树（未来要建的包，不是现状）
├── architecture.md            入口链、包职责、TF 原则
├── simulation.md              怎么起、怎么看
├── commissioning.md           验收流程
├── interfaces.md              话题/服务
├── chassis_protocol.md        真机串口协议
├── frames_and_time.md         TF 树与时间源
├── sentry_urdf_import.md      CAD→URDF 完整方法与坑
├── progress.md                进度流水（含旧包名，属历史）
├── validation/*/              ▢ 每次改动的证据：截图 + metrics.json + probe.py
└── superpowers/plans/*.md     7 份历史计划
```

---

## 5. 运行链（谁 include 谁）

```text
ros2 launch sentry_bringup sim_teleop.launch.py
│  默认值 = config/sim.yaml + sentry_sim/config/simulation.yaml
├── sentry_sim/launch/simulation.launch.py
│   ├── rm_arena/launch/simulation.launch.py
│   │   ├── gzserver（-s libgazebo_ros_init -s libgazebo_ros_factory）+ worlds/arena.world
│   │   ├── gzclient（gui:=true）
│   │   ├── arena_marker → /arena_marker
│   │   └── rviz2（场地预览）
│   └── sentry_sim/launch/spawn_robot.launch.py
│       ├── xacro 展开 sentry_sim.urdf.xacro → 校验 mesh/.so → 改绝对路径
│       ├── sentry_description/launch/description.launch.py
│       │   ├── robot_state_publisher      ← 显示模型（无滚子）
│       │   └── description_publisher      ← 物理模型（latched）
│       ├── static_transform_publisher     world → odom
│       └── spawn_entity                   ← 读那条 latched 话题
└── sentry_motion/launch/motion.launch.py
    └── keyboard_control.py（Qt 窗口 + 同进程看门狗）→ /cmd_vel、/spin_mode
```

## 6. 话题与 TF

| 方向 | 话题 | 发布者 | 订阅者 |
|---|---|---|---|
| 驱动 | `/cmd_vel`、`/spin_mode` | keyboard_control（窗口+看门狗同进程） | omni_drive、gimbal_stabilizer |
| 状态 | `/odom`、`/tf`(odom→base_link)、`/joint_states` | omni_drive | guard、RSP、RViz |
| 云台 | `/gimbal_pose` | gimbal_stabilizer | guard、RViz |
| 模型 | `/sentry_description/robot_description_physics`（latched） | description_publisher | spawn_entity |
| 场地 | `/arena_marker`（latched） | arena_marker | RViz |

```text
world ──(静态)── odom ──(插件)── base_link ── chassis_link ──┬── wheel_1..4_link   （滚子不进 TF）
                                                             └── gimbal_yaw_link ── lidar / camera / gun / muzzle …
```

## 7. 改东西的时候动哪一层

| 你想改 | 只改这里 | 别碰 |
|---|---|---|
| 质量、惯量、尺寸、传感器位置 | `sentry_description/urdf/*` + `config/frames.yaml` | sim 的 xacro |
| 摩擦/接触参数、驱动或云台控制、出生点 | `sentry_sim/urdf/sentry_sim.urdf.xacro`、`src/*.cpp`、`config/simulation.yaml` | description |
| 遥控手感、限速、失联保护 | `sentry_motion/config` + `scripts` | 模型 |
| 默认开哪些窗口、默认速度 | `sentry_bringup/config/sim.yaml` | 各包内部 |
| 场地、预览视角 | `rm_arena/worlds`、`models`、`rviz` | 机器人 |

加一个滚子 / 加一个轮子：`cad_roller`、`cad_wheel` 各加一行调用即可，不用再抄 28 行 XML。

## 8. 验证状态

已做（Windows 侧，无可运行 ROS）：模型指纹 `50168682…ddcde` 与 `tools/tests/test_project_layout.py` 写死的常量一致；
links 119 / joints 118 / continuous 117 / 网格 118 / 球碰撞 112 / `<gazebo>` 119 全部与改前一致；
所有被引用的 mesh 都存在；Python 过 `py_compile`；行宽 ≤ 95（flake8 上限 99）。

**没做**（需要在 Ubuntu 上跑一次）：

```bash
cd ~/RoboVigor/sentinel_ws
./scripts/build.sh
colcon test --packages-select rm_arena sentry_description sentry_sim sentry_motion --event-handlers console_direct+
ros2 launch sentry_bringup sim_teleop.launch.py
```

## 9. 回退

本次改动都在工作区，没有提交：

```bash
cd ~/RoboVigor && git status            # 看清单
git checkout -- .                       # 全部回退（含删除的文件）
git checkout -- sentinel_ws/src        # 只回退源码
```

`tools/import_sentry_cad.py` 重导 CAD 时会把 `chassis.xacro` 覆盖回 3157 行的展开版——
重导之后需要再做一次压缩（可以让我把压缩脚本固定成 `tools/compact_urdf.py`，带等价性自检）。
