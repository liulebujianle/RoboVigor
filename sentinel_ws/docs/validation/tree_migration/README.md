# 目录迁移验收 · 2026-10-29

五个已实现包完成构建安装：rm_arena、sentry_description、sentry_sim、sentry_motion、sentry_bringup。
旧包 sentry_simulation 已不在当前 ament 索引中；旧生成前缀保存在 /tmp/robovigor-pre-tree-migration，
原始 CAD 与桌面 URDF 没有改动。Autoaim 未改动。

## 自动检查

- tools/tests 与 description/motion 的 Python 检查共 17 passed。
- 语义签名检查比较迁移前完整模型与拆分后 Xacro 的全部 link/joint：质量、惯量、碰撞、
  轴线、零位、限制完全一致；仅模型包 URI/文件名随归属变化。
- CAD 导出布局函数的往返检查保留 118 个网格、117 个连续关节、2 个 Gazebo 插件。
- 全部源码 Python flake8 与 pep257 通过；脚本 bash -n 通过。
- colcon test 五包通过；rm_arena 6 passed/1 skipped，description CTest 1/1
  （内部 3 个 CAD 检查），motion CTest 1/1（内部 8 个控制检查），sim CTest 8/8，
  bringup 没有独立测试、由系统运行覆盖。sim 工具默认跳过项保留，不声称运行了 cppcheck 2.7。
- 逐文件确认五包的安装 launch、Xacro、配置、RViz 与源码一致。
- 新统一入口及 scripts/sim.sh 的 launch 参数解析通过。

## 实际运行

独立域 ROS_DOMAIN_ID=181、Gazebo 端口 11477，从安装后的
`ros2 launch sentry_bringup sim_teleop.launch.py gui:=false rviz:=false keyboard:=false`
启动，使用实际安装的 sentry_motion 键盘程序和伪终端送键。

W 前进约 0.377 m，S 后退约 0.355 m；X 底盘累计旋转 7.911 rad，实际云台世界航向最大
偏差 0.001152 rad（约 0.066°）。重复 X、旋转中按云台方向平移、C、空格、键盘失联制动均通过。
查询 Gazebo 确认场地 rmul_2027 和机器人 robovigor_sentry 存在。见 keyboard_metrics.json。
本轮为无界面回归；共享描述与资源路径已验证，没有声称重新截图验收 GUI。

## 审查与边界

独立审查发现 motion 自身需声明 ros2run 和 gnome-terminal，已加入失败→通过的依赖回归并修复。
当前说明中的旧模型路径已更正；其他历史验证记录明确保留历史包名，操作以工作空间 README 为准。

未来 Nav2、地图、真机驱动等按目标提示词分阶段实现，没有创建虚构的地图、传感器或空算法包。
当前必要额外文件（C++ 插件、真实多网格、带材质场地模型）留在正确的职责包中，
与示意树的差别已在 docs/project_tree.md 和 architecture.md 明确记录。
