# 建图与定位

目前有 Odin1 Lite 厂家驱动启动文件和地图服务客户端，完整 SLAM、机器人定位融合还没接入。Gazebo 场地放在 `sentry_map`，建图结果放在 `sentry_maps`，目前地图目录为空。

## 已有代码

- `sentry_sensors/launch/sentry_odin1_lite.launch.py` 调用厂家驱动，默认保留原始坐标，关闭扫描转换。
- `sentry_localization/src/sentry_localization/mapping/sentry_odin_control.py` 提供 normal、slam、save、relocate、remap、export 操作。
- 重定位和 ReMap 先切换模式，再加载已有 `.bin` 地图。服务失败或超时后停止后续步骤。
- 点云转扫描可选择输入话题和 target_frame，实体入口使用非仿真时钟。

建图算法由厂家提供。运行前需要安装与固件匹配的 ROS Driver 和 `manifold-lc-sdk` 算法 deb，并加载厂家驱动与本工作空间环境。

## 使用命令

先启动实体雷达：

```bash
ros2 launch sentry_sensors sentry_odin1_lite.launch.py
```

在驱动主机的另一个终端操作：

```bash
# 开始建图，然后移动设备采集场景
ros2 run sentry_localization sentry_odin_control slam
# 保存不会自动停止建图
ros2 run sentry_localization sentry_odin_control save --path /tmp/odin_map.bin
ros2 run sentry_localization sentry_odin_control normal
# 以下两种按需要选择：重定位，或在已有地图上增量建图
ros2 run sentry_localization sentry_odin_control relocate --path /tmp/odin_map.bin
ros2 run sentry_localization sentry_odin_control remap --path /tmp/odin_map.bin
```

地图路径属于驱动主机。输入文件和输出目录需要提前准备；上面的 `/tmp` 仅供调试，正式结果整理到 `sentry_maps/maps/rmul_2027/odin/`。

默认服务前缀为 `/manifold/device0`，索引不同时用 `--prefix` 指定。客户端默认每次等待和响应超时 30 秒，可用 `--timeout` 调整。超时后先检查设备状态再重试，服务响应成功后继续观察位姿与定位收敛。导出服务沿用厂家拼写 `exploy_map`，文件格式由算法插件决定。

## 后续工作

`sentry_maps` 已建包，但还没有 Nav2 的 YAML/PGM 地图、定位点云或设备 BIN 地图。三维场地网格和 Odin 二进制地图不能直接交给 Nav2 栅格地图服务。

接实机时先测量雷达到机器人的安装变换，检查厂家与机器人 TF、时间同步和实际云台关节状态，再开启扫描转换并调整高度和角度裁剪。还需要实现定位数据适配、地图匹配和 `map → odom`。旧仿真使用的 `world` 也要在这一步与导航 `map` 统一，厂家地图坐标不能直接假定与它重合。

接口见 [interfaces.md](interfaces.md)，坐标约定见 [frames_and_time.md](frames_and_time.md)。厂家流程参考 [Odin 建图与重定位接口](https://manifoldtechltd.github.io/wiki/odin_series/odin1lite/6.%20map%20and%20relocalizaiton%20api.html)。