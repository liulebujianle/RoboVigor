# 当前实际目录与目标对应

此处列出已实现并实际参与构建/启动的目录。大型网格、材质、验证记录及历史计划折叠显示，文件均保留。
目标来源为桌面《算法导航提示词.md》第七节；原目标树摘录见 target_tree.md。

```text
RoboVigor/
├── Autoaim/  # 独立项目，未改动
├── README.md
└── sentinel_ws/
    ├── docs/
    │   ├── superpowers/  # 保留全部实际资源，7 个文件
    │   ├── validation/  # 保留全部实际资源，38 个文件
    │   ├── architecture.md
    │   ├── chassis_protocol.md
    │   ├── commissioning.md
    │   ├── frames_and_time.md
    │   ├── hardware.md
    │   ├── interfaces.md
    │   ├── mapping_and_localization.md
    │   ├── progress.md
    │   ├── project_tree.md
    │   ├── sentry_urdf_import.md
    │   ├── simulation.md
    │   └── target_tree.md
    ├── scripts/
    │   ├── build.sh
    │   └── sim.sh
    ├── src/
    │   ├── rm_arena/
    │   │   ├── docs/
    │   │   │   └── SOURCE_NOTICE.txt
    │   │   ├── launch/
    │   │   │   ├── arena_preview.launch.py
    │   │   │   ├── simulation.launch.py
    │   │   │   └── world.launch.py
    │   │   ├── meshes/  # 保留全部实际资源，0 个文件
    │   │   ├── models/  # 保留全部实际资源，32 个文件
    │   │   ├── resource/
    │   │   │   └── rm_arena
    │   │   ├── rm_arena/
    │   │   │   ├── __init__.py
    │   │   │   └── arena_marker.py
    │   │   ├── rviz/
    │   │   │   └── arena.rviz
    │   │   ├── test/
    │   │   │   ├── test_copyright.py
    │   │   │   ├── test_flake8.py
    │   │   │   ├── test_launch_resources.py
    │   │   │   ├── test_pep257.py
    │   │   │   └── test_resources.py
    │   │   ├── worlds/
    │   │   │   ├── arena.world
    │   │   │   └── empty.world
    │   │   ├── README.md
    │   │   ├── package.xml
    │   │   ├── setup.cfg
    │   │   └── setup.py
    │   ├── sentry_bringup/
    │   │   ├── config/
    │   │   │   └── sim.yaml
    │   │   ├── launch/
    │   │   │   └── sim_teleop.launch.py
    │   │   ├── rviz/
    │   │   │   └── navigation.rviz
    │   │   ├── CMakeLists.txt
    │   │   ├── LICENSE
    │   │   ├── README.md
    │   │   └── package.xml
    │   ├── sentry_description/
    │   │   ├── config/
    │   │   │   └── frames.yaml
    │   │   ├── launch/
    │   │   │   └── description.launch.py
    │   │   ├── meshes/  # 保留全部实际资源，119 个文件
    │   │   ├── rviz/
    │   │   │   └── model.rviz
    │   │   ├── scripts/
    │   │   │   └── description_publisher.py
    │   │   ├── test/
    │   │   │   ├── test_cad_model.py
    │   │   │   ├── test_component_frames.py
    │   │   │   └── test_display_description.py
    │   │   ├── urdf/
    │   │   │   ├── chassis.xacro
    │   │   │   ├── gimbal.xacro
    │   │   │   ├── sensors.xacro
    │   │   │   ├── sentry.urdf.xacro
    │   │   │   ├── sentry_cad.json
    │   │   │   └── sentry_original.urdf
    │   │   ├── CMakeLists.txt
    │   │   ├── LICENSE
    │   │   ├── README.md
    │   │   └── package.xml
    │   ├── sentry_motion/
    │   │   ├── config/
    │   │   │   └── velocity_mux.yaml
    │   │   ├── launch/
    │   │   │   └── motion.launch.py
    │   │   ├── scripts/
    │   │   │   ├── keyboard_control.py
    │   │   │   └── keyboard_window.py
    │   │   ├── test/
    │   │   │   ├── test_keyboard_control.py
    │   │   │   └── test_keyboard_window.py
    │   │   ├── CMakeLists.txt
    │   │   ├── LICENSE
    │   │   ├── README.md
    │   │   └── package.xml
    │   └── sentry_sim/
    │       ├── config/
    │       │   └── simulation.yaml
    │       ├── include/
    │       │   └── sentry_sim/
    │       │       ├── gimbal_math.hpp
    │       │       └── omni_kinematics.hpp
    │       ├── launch/
    │       │   ├── simulation.launch.py
    │       │   └── spawn_robot.launch.py
    │       ├── src/
    │       │   ├── gimbal_stabilizer.cpp
    │       │   └── omni_drive.cpp
    │       ├── test/
    │       │   ├── test_gimbal_math.cpp
    │       │   └── test_omni_kinematics.cpp
    │       ├── urdf/
    │       │   └── sentry_sim.urdf.xacro
    │       ├── CMakeLists.txt
    │       ├── LICENSE
    │       ├── README.md
    │       └── package.xml
    ├── tools/
    │   ├── tests/
    │   │   ├── test_cad_directory.py
    │   │   ├── test_project_layout.py
    │   │   └── test_wheel_geometry.py
    │   ├── vendor/  # 保留全部实际资源，12 个文件
    │   ├── COLCON_IGNORE
    │   ├── import_sentry_cad.py
    │   ├── sentry_frames.py
    │   ├── sentry_model_layout.py
    │   └── sentry_wheels.py
    ├── README.md
    ├── dependencies.repos
    ├── data/  # 本机归档数据
    ├── build/  # 自动生成
    ├── install/  # 自动生成
    └── log/  # 自动生成
```

| 原位置 | 当前维护位置 |
| --- | --- |
| src/sentry_simulation/meshes | src/sentry_description/meshes |
| src/sentry_simulation/urdf/sentry_cad.urdf | description/urdf 下 chassis、gimbal、sensors 和 sentry.urdf.xacro；Gazebo 部分归 sim/urdf/sentry_sim.urdf.xacro |
| src/sentry_simulation/src、include | src/sentry_sim/src、include/sentry_sim |
| src/sentry_simulation/launch/spawn_robot、simulation | src/sentry_sim/launch |
| src/sentry_simulation/scripts/keyboard_control.py | src/sentry_motion/scripts/keyboard_control.py |
| src/sentry_simulation/launch/sim_teleop.launch.py | src/sentry_bringup/launch/sim_teleop.launch.py |
| RoboVigor/tools | sentinel_ws/tools |
| RoboVigor/docs | sentinel_ws/docs |
| RoboVigor/gazebo_arena | sentinel_ws/data/legacy_gazebo_arena（仅归档） |

与文档示意树的必要差异：当前有 118 个真实 CAD 可视网格，保留其独立文件；实际场地使用
STEP/DAE 模型、完整碰撞和纹理，保留 rm_arena/models；sim 的现有 C++ 插件和 motion 的
实际键盘代码必须保留 src/include/scripts/test。新增已验证 sim_teleop 启动入口；未实现
Nav2、真机和地图的目标入口不以空文件冒充功能。

后续包和文件遵守目标树的对应职责，实际实现后再创建；完整状态见 architecture.md。
