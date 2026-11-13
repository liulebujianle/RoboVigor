# 建图与定位状态

本项目已增加Odin1 Lite厂家驱动入口和地图服务客户端，尚未在实体设备上验收。
Gazebo场地、厂家二进制SLAM地图与Nav2二维地图是不同资源，不能互相视为已经生成或接入。

## 当前已有

- Gazebo加载RMUL 2027三维场地，RViz通过场地Marker/RobotModel显示；这不是Nav2栅格地图。
- `sentry_perception/odin1_lite.launch.py`封装官方驱动启动，默认保留原始厂家坐标，关闭未标定的 `/scan`。
- `sentry_perception/scripts/odin_control.py`提供 `normal`、`slam`、`save`、`relocate`、`remap`、`export`操作。
- 重定位/ReMap按厂家流程先切换模式，再加载已有 `.bin`地图；服务失败或超时停止后续步骤。
- 点云转扫描支持选择输入话题与target_frame，实体转换使用非仿真时钟。

这些代码调用官方服务，不包含自研LIO或厂家算法实现。运行建图/重定位须另行取得与固件匹配的
ROS Driver，并在运行驱动的主机安装 `manifold-lc-sdk` 算法deb。只有ROS Driver不能运行完整算法。

## 使用流程

安装并source厂家驱动和本项目后，另一个终端启动实体雷达：

```bash
ros2 launch sentry_perception odin1_lite.launch.py
```

在同一驱动主机执行：

```bash
# 建图，随后移动设备采集场景
ros2 run sentry_perception odin_control.py slam
# 保存地图；保存不会自动停止建图
ros2 run sentry_perception odin_control.py save --path /tmp/odin_map.bin
ros2 run sentry_perception odin_control.py normal
# 用已有地图进行重定位
ros2 run sentry_perception odin_control.py relocate --path /tmp/odin_map.bin
# 或使用已有地图进行增量建图
ros2 run sentry_perception odin_control.py remap --path /tmp/odin_map.bin
```

路径属于运行驱动的主机，输入地图必须存在，输出目录必须存在。默认服务前缀为
`/manifold/device0`；设备索引变更时用 `--prefix`指定，先确认实际序列号与索引。
客户端每次等待/响应默认超时30秒，可用 `--timeout`调整。超时后设备可能已执行操作，
不要仅依据客户端报错立即重复操作。服务成功仅代表请求获接受，定位收敛需观察设备状态和位姿。
导出服务使用厂家拼写 `exploy_map`，实际文件格式由算法插件决定。

## 仍未实现或验收

当前没有生成Nav2 `map.yaml/map.pgm`、导航先验 `prior.pcd`或独立 `sentry_maps`资产包，
也未把DAE/STL当作占据栅格地图。Odin的 `.bin`地图不能直接作为Nav2地图加载。
机器人LIO、先验匹配、导航后端与 `map → odom`融合仍未接入，不发布伪造定位变换。

实体Odin坐标到机器人坐标需要安装标定，并核对厂家TF与机器人TF没有多父节点冲突。
先确认里程计/点云坐标、时间同步和实际云台关节状态，再启用 `/scan`并重新设定高度和角度裁剪。
后续地图、区域和航点应与场地世界坐标保持明确转换关系，不能假定厂家地图天然等同Gazebo world。

详见 [雷达接入说明](../src/sentry_perception/README.md)、[TF与时间](frames_and_time.md)
和[官方建图/重定位流程](https://manifoldtechltd.github.io/wiki/odin_series/odin1lite/6.%20map%20and%20relocalizaiton%20api.html)。
