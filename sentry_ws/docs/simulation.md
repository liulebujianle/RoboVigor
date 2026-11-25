# 仿真笔记

目标环境是 Ubuntu 22.04、ROS 2 Humble、Gazebo Classic 11。先按 [工作空间说明](../README.md) 构建并加载环境，再启动：

```bash
ros2 launch sentry_bringup sentry_sim_teleop.launch.py
```

## 配置位置

| 配置 | 内容 |
| --- | --- |
| `sentry_bringup/config/sentry_sim.yaml` | 窗口开关、键盘速度 |
| `sentry_sim/config/sentry_simulation.yaml` | 机器人名称和出生位置 |
| `sentry_motion/config/velocity_mux.yaml` | 手动输入超时和速度上限 |
| `sentry_perception/config/sentry_pointcloud_to_scan.yaml` | 扫描高度、角度和距离裁剪 |

默认出生点是 (1.25, 6.75, 0.118) m，z 为车体参考点高度。参数文件名虽然叫 velocity_mux，目前只配置键盘进程中的速度看门狗，没有多来源仲裁。

模型和插件从 ament 安装目录读取，修改后重新构建并 source。固定车体在 `sentry_description`，仿真 Xacro 和原生插件在 `sentry_sim`。旧 CAD 提取工具保留作来源工具，重新生成前先检查与现有模型的差异。

## 场地和机器人

场地由 `sentry_map` 加载，显示资源为 RMUL 2027 DAE，碰撞采用 29 个盒体，包含地台、围挡和平台。保留的 `field_collision.stl` 没有被当前 SDF 引用。资源来源和转换工具见 [场地说明](../src/sentry_map/README.md)。

车体默认使用轻量几何，四个圆柱轮以方向摩擦近似全向运动。四轮、yaw 和 pitch 共六个活动关节，Gazebo 插件以有限力矩驱动。车体上部缺少碰撞体，质量、惯量、摩擦和控制参数仍是仿真估计。

仿真里程计使用 Gazebo 世界真值，TF 仍为 `world → odom → base_link`。导航 `map` 与定位融合还没接入。

## 普通键盘

当前使用 Qt 键盘窗口。W/S 前后、A/D 横移、Q/E 旋转，X 开小陀螺，C 或空格全停。默认平移 0.8 m/s、旋转 1.5 rad/s、小陀螺 3.0 rad/s。松开移动键停止对应输入，小陀螺保持到 C 或空格。

键盘窗口失焦不会主动停车，关闭窗口会发全停。输入看门狗默认超时 0.5 秒，底盘插件也有指令超时处理。实际减速距离、窗口事件和小陀螺平移需要在 Ubuntu 中检查。

`keyboard:=false` 关闭输入窗口；当前没有选手视角。原模型里的相机参考系仍保留。

## 雷达和扫描

两台雷达都使用 `gpu_ray`，默认显示射线。Odin 从右侧 TX 窗正前方的亚克力外表面沿局部 +X 扫描，发布 `/lidar/points`；Mid-360S 扫描一整圈，发布 `/mid360s/points`。扫描范围、点云坐标系和检查命令见[仿真雷达配置说明](../src/sentry_sim/README.md)。

`perception:=false` 关闭点云到 `/scan` 的转换，激光传感器仍运行。默认扫描在 base_link 中保留 0.10–0.60 m 高度、±60° 角域；云台转动时可能裁掉部分点云，后面接导航时需要重新设定。仿真没有完整复现真实光照、反射率、RGB、IMU 或厂家 SLAM。

实体雷达从 `sentry_sensors` 单独启动，见 [硬件记录](hardware.md)。

## 排错

先退出占用同一端口的旧 gzserver，再启动本工程。启动文件负责设置资源路径，直接裸跑 gzserver 时需要自行配置。关闭 Gazebo 客户端会结束组合启动；gzserver 异常退出时其他窗口的清理情况仍需检查。

`gui:=false` 关闭 Gazebo 界面，但 gpu_ray 仍可能需要显卡或显示渲染环境。编译、测试、TF 和停车检查见 [调试步骤](commissioning.md)，旧数据保存在 `validation/`。