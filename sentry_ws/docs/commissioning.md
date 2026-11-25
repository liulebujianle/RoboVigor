# 调试步骤

在 Ubuntu 22.04、ROS 2 Humble、Gazebo Classic 11 中检查。下面的命令在 `sentry_ws` 目录执行，先加载 ROS 环境。

## 编译和启动

```bash
source /opt/ros/humble/setup.bash
colcon list --base-paths src
colcon build --symlink-install --base-paths src
source install/setup.bash
ros2 pkg prefix --share sentry_description
ros2 launch sentry_bringup sentry_sim_teleop.launch.py
```

包列表应有 13 个包，模型路径应指向本工作空间的安装目录。启动后检查场地、一辆机器人、RViz 和普通键盘窗口。

## 手动控制

1. 不按键时确认车停在出生点，小陀螺关闭。
2. 点击控制窗口，分别按住、松开 W/S、A/D，再试 Q/E，检查运动方向和停车。
3. 按 X 开启小陀螺，按住 W 检查平移方向与云台世界航向。松开 W 停止平移，C 或空格全停。
4. 关闭控制窗口检查停车，再关闭 Gazebo，检查相关进程是否退出。

切换到其他窗口会松开按住的移动键。X 开启的小陀螺可以用 C 或空格关闭。四轮应独立旋转，默认模型没有单独的滚子刚体。

## 数据检查

检查 `/odom`、`/joint_states`、`/lidar/points`、`/mid360s/points`、`/scan` 和 TF。仿真仍使用 `world → odom → base_link`，导航 `map` 的连接需要后续定位模块完成。

启动失败时先看 launch 日志，再检查安装目录下的网格、sentry_sim 安装前缀中 `lib/` 下的插件、物理描述话题和 Gazebo 服务。`perception:=false` 应只关闭 `/scan` 转换，`keyboard:=false` 应关闭输入窗口。

```bash
colcon test
colcon test-result --verbose
python3 -m pytest -q tools/tests
```

测试结果与界面、接触、停车效果分别记录到 `docs/validation/`。旧版本的通过数量保留在对应历史记录中。这次目录调整后的 ROS/Gazebo 运行还需要完成以上检查；实车按传感器、定位、导航、通信的顺序逐项联调。