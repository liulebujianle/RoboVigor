# 仿真维护

入口见工作空间 README。配置选择是显式的：bringup/config/sim.yaml → 系统默认开关和键盘速度；
sentry_sim/config/simulation.yaml → 出生 xyz 与模型名；motion/config/velocity_mux.yaml → 当前速度保护参数。
launch 参数可覆盖公开的默认值；配置文件不会仅凭文件名自动覆盖其他配置。

机器人平台：description/urdf/sentry.urdf.xacro 引用 chassis、gimbal、sensors。
仿真：sim/urdf/sentry_sim.urdf.xacro 引用平台并添加实际 Gazebo 插件及接触参数。
spawn 在安装目录展开 Xacro，解析网格为安装资源 file URI、插件为安装 lib 绝对路径，
再把同一字符串交给 description.launch.py 发布及 spawn_entity 使用。

质量、摩擦和电机参数尚未按实车标定；滚子碰撞为拟合球。详见 validation/wheel_physics。
场地是现有带材质的 STEP/DAE，保留 rm_arena/models/rmul_2027 完整模型和纹理。
目标树里的旧 rmul_2027.stl 不是当前显示模型，不用它替换已经验证的资源。

重新提取真实 CAD，在工作空间根目录：
`python3 tools/import_sentry_cad.py /path/to/大小yaw哨兵`。
工具同时更新 description 网格、Xacro/元数据以及 sim 的 Gazebo 扩展，再重新构建。

## 键盘和启动故障

默认使用 RoboVigor 键盘控制窗口，不依赖终端自动重复。按住移动键连续运动，松开停止；
启动时小陀螺关闭，X 开启，C/空格或切换窗口全停。小陀螺中的平移按锁定的云台世界方向转换。
Qt 窗口是 launch 直接管理的子进程，原始输入按 control_session 隔离。

若已有旧 gzserver 占端口，新服务会报告 Address already in use；本次补充服务退出就关闭整套
launch，防止 RViz/客户端继续显示缺少真实状态的画面。先正常关闭旧启动再运行 scripts/sim.sh。
不要绕过 rm_arena 的 launch 手工裸跑 gzserver，否则不会得到该包的场地模型搜索路径。

小陀螺直线控制以实际 odom 位置锁定本次平移的世界参考线，100 Hz 重算车体方向，
横向纠偏增益 6 s⁻¹、附加横向速度限 0.25 m/s；总输出仍受 max_linear 限制。
松开移动键后仍在小陀螺中维持横向制动纠偏，C/空格/失联时全部输出停止。
车辆仍靠轮地摩擦和有限力矩驱动，存在真实制动距离和小量滑移。
关闭 Gazebo 窗口会退出整套启动，清理后台服务与键盘子进程。


当前轮子与相机/雷达一样是原生TF中的独立部件，四个wheel_i_link位于真实轮轴中心并随角度旋转。
RViz直接订阅 /robot_description 和公开TF。Gazebo生成订阅完整的
/sentry_description/robot_description_physics，仍使用全部112个被动滚子物理。
没有 wheels_link 聚合底部轴，也没有 MarkerArray 车轮动画。详见 frames_and_time.md。
