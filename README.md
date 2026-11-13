# RoboVigor

ROS 2 哨兵机器人仿真与控制工程，包含 RMUL 2027 场地、轻量四轮全向模型、
枪口第一人称视角控制，以及 Odin1 Lite 雷达仿真和实体设备接入入口。

- [工作空间说明与完整启动步骤](sentinel_ws/README.md)
- [Odin1 Lite：驱动、点云、建图与重定位](sentinel_ws/src/sentry_perception/README.md)
- [FPS 与旧键盘控制](sentinel_ws/src/sentry_motion/README.md)
- [场地资源与碰撞说明](sentinel_ws/src/rm_arena/README.md)
- [系统结构与功能边界](sentinel_ws/docs/architecture.md)
- [独立 Autoaim 工程](Autoaim/README.md)

## 启动仿真

目标环境：Ubuntu 22.04、ROS 2 Humble、Gazebo Classic 11、RViz2、PyQt5。
在已安装 ROS 和依赖的机器上：

```bash
git clone https://github.com/liulebujianle/RoboVigor.git
cd RoboVigor/sentinel_ws
./scripts/build.sh
./scripts/sim.sh
```

默认使用 FPS 窗口：画面和位姿就绪后点击捕获鼠标，鼠标控制云台朝向，WASD 按当前
实际视角移动，X 开启小陀螺，C/空格停车，Esc 释放鼠标并停车。
旧键盘模式可用 `./scripts/sim.sh fps:=false`。

## 当前状态

仓库包含仿真配置、控制代码和离线回归测试。实体 Odin1 Lite 需要另行取得与固件
匹配的厂家驱动；建图和重定位还需安装 `manifold-lc-sdk`。新雷达安装位置暂沿用
旧 CAD 坐标作仿真占位，实车必须标定；厂家算法及其地图不等于已完成 Nav2 导航。

2026-11-14 更新包含 FPS 控制、场地资源恢复及 Odin1 Lite 替换。
离线测试结果和 Ubuntu/Gazebo/实体设备的待验收项目见
[更新验证记录](sentinel_ws/docs/validation/update_2026-11-14.md)。历史验证只对应当时版本。
