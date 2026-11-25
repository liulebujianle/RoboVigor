# sentry_perception

仿真发布两路 `sensor_msgs/msg/PointCloud2`。在总启动的 RViz 里，青色点来自 Odin，橙色点来自 Mid-360S。

| 雷达 | 点云话题 | 坐标系 | 仿真采样 |
| --- | --- | --- | --- |
| Odin1 Lite | `/lidar/points` | `odin1_lite_link` | 240 × 180，120° × 90°，10 Hz |
| Mid-360S | `/mid360s/points` | `mid360s_link` | 每帧 500 × 40 条射线，水平一整圈，垂直 −7° 到 +52°，10 Hz |

Odin 的仿真量程为 0.15–25 m，按 10% 反射率、照度低于 50 klx 的标称场景设置。固定 0.03 m 高斯标准差是对厂家 5 m 测试条件的近似。[Odin1 Lite 技术参数](https://manifoldtechltd.github.io/wiki/odin_series/odin1lite/12.%20Technical%20Specifications_.html)

Mid-360S 仿真使用规则射线网格近似视场与每秒 20 万次采样。实际设备的扫描轨迹随时间变化。仿真量程取 0.1–40 m，40 m 为 10% 反射率、100 klx 条件下的典型值，实物截止量程为 100 m。两台雷达的有效回波数都随场景变化。[Livox Mid-360S 技术参数](https://www.livoxtech.com/cn/mid-360s/specs)

`/scan` 默认仅使用 Odin 点云。可以单独启动转换器。

```bash
ros2 launch sentry_perception sentry_pointcloud_to_scan.launch.py
```

高度带、角域和量程配置在 `config/sentry_pointcloud_to_scan.yaml`。`cloud_topic` 可指定
其他输入话题，点云坐标系到 `target_frame` 的 TF 需有效。实物雷达接入后还需核对
安装外参和高度范围。`src/sentry_perception/filtering/` 目前仅有空模块。

实体 Odin 的厂家驱动入口位于 `sentry_sensors`，Odin 地图服务客户端位于
`sentry_localization`。
