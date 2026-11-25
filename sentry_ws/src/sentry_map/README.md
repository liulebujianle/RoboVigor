# sentry_map

RMUL 场地模型、Gazebo 场景、RViz Marker 和模型转换工具。Python 代码位于
`src/sentry_map/`，场景位于 `scenes/sentry_map.sdf`，完整模型树位于 `models/`。
场景使用 SDF 的 `<world>` 元素，坐标系为 `world`。

在 `sentry_ws` 中构建并启动：

```bash
colcon build --base-paths src --packages-select sentry_map
source install/setup.bash
ros2 launch sentry_map sentry_map.launch.py
```

`scene:=/path/to/scene.sdf` 指定场景；`gazebo`、`gui`、`rviz` 开关和
`rviz_config` 设置视图。也可单独启动预览或 Gazebo 场地：

```bash
ros2 launch sentry_map sentry_map_preview.launch.py
ros2 launch sentry_map sentry_map_server.launch.py
```

Marker 节点入口为 `ros2 run sentry_map sentry_arena_marker`，沿用
`/arena_marker` 话题、`world` 坐标系与持久化 QoS。RViz 配置为
`rviz/sentry_map.rviz`。

模型来源为 RoboVigor 提交 `e2ddcdb1ebbef47eaeae3490fe0c897d69083659`。
模型、纹理、归档源码与来源说明保持原资源内容；上游历史路径见
`docs/SOURCE_NOTICE.txt`。`model.sdf` 保留 29 个封闭碰撞盒；外观、UV 与
材质保持现有版本，围挡压顶已有的加载兼容修正也保留。

正常启动直接加载已有模型。需要生成或恢复资源时，单独运行以下工具；
`--out` 指定输出目录，转换结果会覆盖该目录下的同名文件：

```bash
ros2 run sentry_map sentry_restore_github_field --out /path/to/rmul_2027
ros2 run sentry_map sentry_stl_to_field --stl /path/to/field.stl --out /path/to/model
ros2 run sentry_map sentry_step_to_field --step /path/to/field.stp --out /path/to/model
ros2 launch sentry_map sentry_step_field.launch.py step:=/path/to/field.stp out:=/path/to/model
```

恢复工具读取本地归档，`--out` 目录中要已有 `source/github_*` 文件。它不会从
GitHub 下载资源，也不能直接恢复到没有归档的新目录。

STEP 转换需要另装 `cascadio` 与 `trimesh`。转换成功后才启动 Gazebo 和 RViz；
默认输出指向已安装模型目录。使用自定义 `out` 时，还需使场景和
`GAZEBO_MODEL_PATH` 指向该模型所在目录。

资源、材质和转换测试位于 `test/`。Gazebo 接触和渲染效果仍需在 Ubuntu/ROS
环境验证。机器人上部显示件未全部配置碰撞体，见
[sentry_description](../sentry_description/README.md)。
