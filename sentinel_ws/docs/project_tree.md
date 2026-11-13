# 当前源码导航

此页概述2026-11-14实际源码。历史规划见target_tree.md，当前功能边界见architecture.md。
大型网格、材质和历史验证目录在此折叠，不用文件数表示运行完成度。

```text
RoboVigor/
├── README.md
├── Autoaim/                         # 独立Python工程
└── sentinel_ws/
    ├── README.md
    ├── scripts/build.sh, sim.sh     # 构建/仿真入口
    ├── docs/
    │   ├── architecture.md          # 当前职责和功能边界
    │   ├── frames_and_time.md       # TF/时钟
    │   ├── interfaces.md            # 话题接口
    │   ├── simulation.md            # 维护和运行限制
    │   └── validation/              # 当前更新记录与分版本历史证据
    ├── tools/
    │   ├── verify_offline.py        # 可移植离线测试，显式排除ROS/Linux检查
    │   ├── tests/                  # 工具/源码布局回归
    │   └── ...                     # CAD提取和模型生成工具
    └── src/
        ├── rm_arena/
        │   ├── launch/             # 场地、预览、STEP重建
        │   ├── models/rmul_2027/    # DAE显示、SDF盒体碰撞、source归档
        │   ├── rm_arena/           # Marker、STEP/STL转换、GitHub资源恢复
        │   ├── test/
        │   └── README.md
        ├── sentry_description/
        │   ├── config/frames.yaml  # CAD名义参考与新雷达占位声明
        │   ├── urdf/               # chassis/gimbal/sensors及主Xacro
        │   ├── meshes/             # 保留CAD来源资源
        │   ├── launch/, scripts/   # RSP与物理描述发布
        │   ├── test/, rviz/
        │   └── README.md
        ├── sentry_sim/
        │   ├── src/                # omni_drive、gimbal_stabilizer
        │   ├── include/, test/
        │   ├── urdf/
        │   │   ├── sentry_sim.urdf.xacro
        │   │   └── gazebo/lidar.xacro, fps_camera.xacro
        │   ├── config/, launch/
        │   └── README.md
        ├── sentry_motion/
        │   ├── scripts/            # fps_control、fps_logic、keyboard_control
        │   ├── launch/motion.launch.py
        │   ├── config/, test/
        │   └── README.md
        ├── sentry_bringup/
        │   ├── launch/sim_teleop.launch.py
        │   ├── config/, rviz/
        │   └── README.md
        └── sentry_perception/
            ├── launch/pointcloud_to_scan.launch.py
            ├── launch/odin1_lite.launch.py
            ├── scripts/odin_control.py
            ├── config/pointcloud_to_scan.yaml
            ├── test/
            └── README.md
```

旧sentry_simulation包已退出，统一入口为sentry_bringup/sim_teleop.launch.py。
机器人描述由sentry_description维护，Gazebo扩展由sentry_sim维护；场地转换不应改机器人。
Odin1 Lite厂家驱动、算法SDK以及实车标定为外部依赖，不包含在此目录树中。
