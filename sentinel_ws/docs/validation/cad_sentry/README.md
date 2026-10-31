# 用户 CAD 整车验证（2026-10-29）

实际运行安装入口：`ros2 launch sentry_simulation simulation.launch.py`。
测试使用独立 ROS 域 178、Gazebo 端口 11474，测试进程已关闭。

- 整车 `robovigor_sentry` 在 Gazebo 中生成成功，见 gazebo-robot.txt。
- 同一安装 mesh file URI 通过 robot_description 提供给 Gazebo 与 RViz。
- 里程计与 world → body_link TF 通过，实测位置 (1.25,6.75,0.1164)。
- Gazebo 真实窗口已人工检查图像：场地、完整车辆同时可见，见 gazebo.png。
- RViz 进程成功启动，OpenGL 初始化正常，模型描述和完整 TF 可接收；
  没有启动/资源加载错误。RViz 截图受桌面窗口遮挡影响，未作为画面验收证据保存。
- Ctrl+C 后所有本次节点正常退出；修复了 Marker 重复关闭 ROS 上下文报错。
- rm_arena 包 pytest 6 passed、1 skipped；sentry_simulation 包 pytest 5 passed；
  目录解析回归 1 passed。sentry_simulation 完整 CTest 6/6 passed，
  colcon test-result 汇总 15 tests、0 errors、0 failures。
- 场地子进程环境回归在沙箱中出现间歇进程回收超时，已在正常环境重跑：6 passed、1 skipped。
- 首次 xmllint 在沙箱内因不能访问 schema 失败，已在沙箱外重跑通过。
  原有中文文档字符串句号引起的 pep257 失败已修正并重跑通过。
- 全仓 pytest 仍在 Autoaim 收集时因缺少 gxipy 失败，不是此仿真入口依赖。

车体来自用户 CAD 缓存，保存姿态固定；碰撞、质量和惯量为临时仿真假设。
原文件和来源、生成方法见 ../../sentry_urdf_import.md。
