# Odin1 Lite 雷达接入

本项目现使用一个 Manifold Odin1 Lite 激光仿真。`lidar_link` 是主雷达，原
`lidar_aux_link` 只保留兼容TF，不显示旧雷达，也不创建第二个扫描传感器。
现有安装位置来自旧CAD，仅作仿真占位；不是Odin1 Lite的安装标定。

## 仿真

```bash
source /opt/ros/humble/setup.bash
colcon build --base-paths src --packages-up-to sentry_bringup
source install/setup.bash
ros2 launch sentry_bringup sim_teleop.launch.py
```

`sentry_sim/urdf/gazebo/lidar.xacro`：10Hz、240×180、水平120°、垂直90°、
0.15–25m，输出 `/lidar/points` (`sensor_msgs/PointCloud2`, `lidar_link`)。
本包转换为 `/scan`，用仿真时钟。改变测距范围时必须同时调整
`config/pointcloud_to_scan.yaml`。分辨率0.01m不等于精度；未模拟噪声、反射率、
光照、置信度、RGB、IMU和厂家SLAM。外形为58mm深×69mm宽×69mm高的近似盒体，
外壳底面与雷达参考原点重合仅为显示假设；没有新增质量来重复计算整车CAD惯量。

## 实体雷达

在Ubuntu22.04/ROS2 Humble或Ubuntu24.04/ROS2 Jazzy运行。按官方第7章从厂家取得
匹配固件的ROS Driver，使用其 `script/build_ros2.sh` 编译，并source驱动工作空间。
v3.x固件使用v3.x驱动，本接入按文档v3.7.0接口编写。
建图/重定位还需要主机安装官方 `manifold-lc-sdk` 算法deb（官方第7.10/9章），
单独编译ROS Driver不会安装算法。厂家仓库需要售后账号，本仓库不包含这些二进制。

设备默认IP为192.168.1.251，PC有线网卡需处于192.168.1.x/24。
完成硬件连接后，source驱动及本项目的install/setup.bash：

```bash
ros2 launch sentry_perception odin1_lite.launch.py
```

默认启动厂家RViz，原始数据在 `/manifold/device0/cloud/raw`；其余图像、IMU和里程计
由官方驱动提供。本入口不启动Gazebo、运动控制器或机器人TF发布器。
`topic_prefix`默认manifold，`device_index`默认0（仅选择扫描订阅设备，不控制发现顺序）。
多设备时通过device_online确认序列号和索引；不要对未确认设备调用地图服务。

保留原始点云坐标名 `lidar`（raw_frame_id），不直接改名为机器人 `lidar_link`。
必须使用实际标定建立机器人到厂家雷达TF，并检查厂家TF树无重复父节点；
雷达安装在可转云台上时还必须提供实际云台关节状态。每台设备的相机外参应从
`get_calibration`或Dashboard获取，不要复制手册里的示例序列号标定。

默认关闭 `/scan`，防止未标定的点云进入导航。标定和高度切片确认后开启：

```bash
ros2 launch sentry_perception odin1_lite.launch.py perception:=true
```

也可以独立转换已有点云：

```bash
ros2 launch sentry_perception pointcloud_to_scan.launch.py \
  use_sim_time:=false cloud_topic:=/manifold/device0/cloud/raw target_frame:=base_link
```

`target_frame`必须与消息frame_id有有效TF。高度0.10–0.60m及±60°角度裁剪均在
target_frame中计算，需按实车和云台朝向重新设定。本接入不发布Nav2的map→odom，
避免与现有定位源冲突；机器人定位融合属于后续实车标定验收。

本包只提供点云转扫描和厂家驱动/服务的接入。未实现车体点云过滤、地形分析、
Nav2导航或自动避障；实体启动不会自动启动机器人运动控制。

## 建图、地图保存、重定位

以下命令在运行驱动的同一主机上执行（路径也属于该主机），使用真实ROS服务；
不会在Gazebo中伪造厂家算法。先确保驱动、设备和算法deb均可用。

```bash
# 开始SLAM建图，移动设备采集环境
ros2 run sentry_perception odin_control.py slam
# 保存地图，不会自动停止建图；输出目录必须已经存在
ros2 run sentry_perception odin_control.py save --path /tmp/odin_map.bin
# 回到正常模式
ros2 run sentry_perception odin_control.py normal
# 先切换重定位模式，再加载地图；任一步失败立即停止
ros2 run sentry_perception odin_control.py relocate --path /tmp/odin_map.bin
# 使用已有地图增量建图
ros2 run sentry_perception odin_control.py remap --path /tmp/odin_map.bin
# 导出：实际格式由厂家算法插件决定
ros2 run sentry_perception odin_control.py export --path /tmp/odin_export.bin
```

其他设备添加 `--prefix /manifold/device1`。每次服务等待/响应默认超时30秒，可用
`--timeout 60`更改。超时不代表设备未执行，重试前检查设备状态。服务成功表示请求
被接受，不能当作重定位已收敛的证明；观察定位状态及位姿输出。重定位地图是厂家
二进制`.bin`，不是Nav2二维栅格地图YAML/PGM。导出服务拼写确为 `exploy_map`。

## 官方依据与差异

- [技术参数](https://manifoldtechltd.github.io/wiki/odin_series/odin1lite/12.%20Technical%20Specifications_.html)：
  240×180、120°×90°、最高10FPS，0.15m起；25m需10%反射率且光照<50klux，
  50m需90%反射率且光照<500lux。默认仿真采用25m。
- [数据接口](https://manifoldtechltd.github.io/wiki/odin_series/odin1lite/5.%20Data%20output_.html)：
  原始点云章节写256×192，并含intensity、confidence、offset_time。
  仿真使用名义240×180；Gazebo点云不保证包含厂家扩展字段。实机以消息width/height/fields为准。
- [驱动安装](https://manifoldtechltd.github.io/wiki/odin_series/odin1lite/7.%20Odin1Lite%20Quick%20start%20for%20ubuntu.html)
- [地图服务](https://manifoldtechltd.github.io/wiki/odin_series/odin1lite/6.%20map%20and%20relocalizaiton%20api.html)

Windows端离线检查不能替代Ubuntu上的colcon编译、Gazebo GPU扫描测试和实体设备联调。
离线测试在 `test/test_odin_config.py` 和 `test/test_odin_control.py`，覆盖仿真与扫描
参数一致性、地图路径校验、服务步骤顺序及失败响应处理；不证明设备已联网或重定位已收敛。
