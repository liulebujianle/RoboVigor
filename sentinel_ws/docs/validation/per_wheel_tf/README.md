# 四个独立轮轴 TF 验证（2026-10-30）

当前要求：删除 wheel_visuals.py 和底部 wheels_link；四个主轮各有一个独立轮轴坐标系，随实际关节角度旋转。此记录替代 public_frames 和 rviz_wheel_center 中的历史方案。

实现位于 sentry_description：chassis.xacro 保留四个连续轮关节；description.launch.py 将滚子外观合入所属主轮，原生 robot_state_publisher 从实际 JointState 发布 wheel_1_link 至 wheel_4_link。RViz 使用标准 RobotModel 和 TF。Gazebo 从独立的完整物理描述启动，仍保留 112 个被动滚子自由度；RViz 中滚子采用相对轮毂的名义姿态，不单独显示滚子 TF。雷达、摄像头、枪管及枪口坐标系保留。

验证结果：

- 完整模型 117 个连续关节，显示模型 5 个连续关节，118 个网格完整保留；每个车轮 29 个网格。
- 四个轮轴 TF 的位置等于原始关节中心，旋转逐时间戳与实测 JointState 匹配（四元数误差阈值 1e-5）。
- 前进实测位移 0.325 m，四轮 TF 均旋转约 2.86–2.90 rad。
- 公共 TF 中有四个主轮，没有 wheels_link 或 roller_*；旧车轮 Marker、私有完整 TF 发布均已消失。
- 31 个源码测试通过；colcon test 五个相关包完成，汇总 36 tests、0 errors、0 failures、7 skipped。全工作区 test-result 扫描另遇到旧导航构建目录的缺失 package.xml；与当前五包无关。
- description 的 flake8 和 pep257 均通过。
- 默认域完整 launch 重启成功，Gazebo 场地和机器人加载成功，RViz 标准描述/TF 订阅已核对，截图见 desktop.png。

启动方式：

```bash
cd /home/ethan/RoboVigor/sentinel_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch sentry_bringup sim_teleop.launch.py
```
