# 硬件记录

当前使用的雷达是 Manifold Odin1 Lite。工程中有仿真模型、厂家驱动启动文件和地图服务客户端，实机网络、驱动运行和安装外参还需要联调。旧 Mid-360 名称保留在原始 CAD 和历史记录中。

## Odin1 Lite

仿真参数为 10 Hz、240×180、120°×90°、0.15–25 m。主雷达 `lidar_link` 沿用旧 CAD 安装位置；辅助 `lidar_aux_link` 只保留参考系。外形近似为深 58 mm、宽 69 mm、高 69 mm，外壳显示位置还没有实测标定。

实体入口是：

```bash
ros2 launch sentry_sensors sentry_odin1_lite.launch.py
```

启动文件按厂家 v3.7.0 文档接口编写。使用前先核对设备固件和对应驱动版本，安装、编译并 source `odin_ros_driver_rev1`。建图与重定位还需要在驱动主机安装 `manifold-lc-sdk` 算法 deb，这些依赖没有附带在工程里。

文档记录的默认 IP 是 `192.168.1.251`，PC 有线网卡应在同网段。现场先核对设备序列号、当前 IP 和固件。原始点云保留厂家 `lidar` 坐标，机器人安装变换另行测量。

厂家文档第 12 章的名义深度为 240×180，第 5 章原始点云写 256×192；当前仿真采用前者，实机按消息的 width、height、fields 检查。仿真不包含反射率、光照、置信度、RGB、IMU 和厂家 SLAM 的完整行为。真实 25 m 和 50 m 测距对应不同反射率、光照条件。

驱动与点云参数见 [驱动启动文件](../src/sentry_sensors/launch/sentry_odin1_lite.launch.py) 和 [sentry_perception](../src/sentry_perception/README.md)，地图操作见 [建图定位](mapping_and_localization.md)。

## 机器人

四轮布局和部件名义坐标来自 CAD，默认仿真使用基础几何和方向摩擦近似。质量、惯量、摩擦和控制增益需要实测后标定。pitch 是仿真中的活动关节，实车 TF 要使用硬件反馈。

目标仿真环境为 Ubuntu 22.04、ROS 2 Humble、Gazebo Classic 11。底盘通信、电机反馈、编码器里程计、定位融合和实车总启动仍待接入。当前只通过普通键盘控制仿真车。
