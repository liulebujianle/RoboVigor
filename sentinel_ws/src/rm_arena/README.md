# rm_arena

ROS 2 Humble / Gazebo Classic 11 的 RMUL 2027 场地包。场地 world、
STEP 转换网格、纹理和 RViz 配置随包安装，无需依赖仓库外层的
`gazebo_arena`，也不需要设置 `ROBOVIGOR_ROOT`。

完整仿真（场地、用户 CAD 机器人、Gazebo 和 RViz）在 `sentinel_ws` 中启动：

```bash
source /opt/ros/humble/setup.bash
colcon build --packages-select rm_arena sentry_simulation
source install/setup.bash
ros2 launch sentry_simulation simulation.launch.py
```

以下入口仅启动场地，不生成机器人：

```bash
source /opt/ros/humble/setup.bash
colcon build --packages-select rm_arena
source install/setup.bash
ros2 launch rm_arena simulation.launch.py
```

仅 Gazebo：`ros2 launch rm_arena simulation.launch.py rviz:=false`。
仅 RViz：`ros2 launch rm_arena simulation.launch.py gazebo:=false`。
两个开关均默认为 `true`。Gazebo 加载 ROS 初始化和 factory 插件，
提供 `/clock` 及模型生成服务；机器人由 `sentry_simulation` 单独生成。
完整入口还发布 `/robot_description` 和 `world → odom → base_link` TF，
RViz 的 RobotModel 使用同一份机器人 URDF；Grid 以 (6,4) 为中心覆盖场地。

Gazebo 优先从安装目录的 `models` 查找场地，同时保留已有
`GAZEBO_MODEL_PATH`。RViz 的 `/arena_marker` 使用同一安装目录的
`step_textured.dae`，启用内嵌材质。坐标系为 `world`，内场西南角为
原点，X 向东、Y 向北、Z 向上，单位米；内场 12 × 8 m。

验证：

```bash
colcon test --packages-select rm_arena --event-handlers console_direct+
colcon test-result --verbose
```

资源测试会将 setuptools 的实际数据文件清单复制到临时安装目录，检查
world → model → mesh → texture 引用是否完整，并检查 ROS/Python 版本一致。
图形界面外观、机器人全地形运动和导航效果仍需在实际运行环境验收。

本包代码声明 Apache-2.0；官方场地几何、纹理和标识的权利归原权利人，
不因代码许可证而重新授权，见 [来源说明](docs/SOURCE_NOTICE.txt)。
