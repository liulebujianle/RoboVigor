# rm_arena：RMUL 2027 场地

默认场地以 https://github.com/liulebujianle/RoboVigor 提交 `e2ddcdb1ebbef47eaeae3490fe0c897d69083659` 为准。
按用户确认恢复完整原材质：灰色底图、深灰围挡、白色压顶、红蓝标记、浅蓝侧面与绿色平台。
配色来源是该提交的 `rm_arena/step_to_field.py` 中 PALETTE、materials_for，
实际场地 DAE 的材质/UV 与 official_top.png 贴图；不使用上一版自选的绿灰配色。

## 碰撞与外观

- model.sdf 恢复该 GitHub 提交的原文件：29个封闭 box 碰撞体，static=true。
- 两处窄挡板 c10_h0.40 / c11_h0.40 使用0.2×1.95×0.4米封闭碰撞盒。
- 碰撞盒是 GitHub 版本的几何近似，不代表精确 STL 表面；部分区域被当成实心区域。
- 外观恢复 GitHub 的 field.dae 与贴图，保留顶点和UV坐标及所有材质值。
- 为 Gazebo Classic 修复交错索引、材质/UV绑定和重复节点ID。
- 只对已确认向内的155面白色围挡压顶修正绕序与法线，使顶盖朝上。
- 场地恢复工具只处理场地资源；机器人、雷达和控制逻辑分别由其他包维护。

## Ubuntu 更新

先关闭旧仿真，在 `sentinel_ws` 工作区执行完整更新构建：

```bash
source /opt/ros/humble/setup.bash
colcon build --base-paths src --packages-up-to sentry_bringup
source install/setup.bash
ros2 launch sentry_bringup sim_teleop.launch.py
```

如果只改场地资源，可改用 `colcon build --base-paths src --packages-select rm_arena`；
本次同时更新了FPS、机器人描述和Odin1 Lite接入，完整更新时应构建组合入口的依赖包。
在 Gazebo 的 View → Collisions 中检查挡板碰撞，低速接近挡板验收实际接触效果。
如果窗口仍显示旧地图，先完全退出旧仿真，再确认 source 的是这次工作区的 install/setup.bash。

## 复现和验证

固定参考文件保存于 models/rmul_2027/source/github_*，包括配色原代码。
正常启动不下载、不转换地图。如需从归档重新生成默认场地：

```bash
python3 src/rm_arena/rm_arena/restore_github_field.py --out src/rm_arena/models/rmul_2027
colcon build --base-paths src --packages-select rm_arena
```

旧 stl_to_field、step_to_field 和 step_field.launch.py 作为显式历史工具保留，运行它们重新转换会覆盖当前默认地图。
离线配置/材质/资源检查位于 `test/`；真实 Gazebo 物理接触与GPU雷达需要目标Ubuntu验收。

## 截图中的上部重叠限制

`sentry_description/urdf/gimbal.xacro` 的云台没有 collision 元素；相机和枪管参考模型
也没有碰撞体。这些外观与障碍物重叠，不能只归因于场地。当前机器人仍使用
底盘/车轮碰撞与上部简化显示，不能保证云台、相机或枪管不会出现视觉穿模。
机器人模型限制见 [sentry_description](../sentry_description/README.md)。
