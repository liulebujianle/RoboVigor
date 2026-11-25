# sentry_description

导航模型沿用这版 SolidWorks 总装的轮廓，底盘、转台、四个全向轮和两台雷达各用一个轻量显示网格。每个轮子只占一个 TF，滚子跟着所属轮子一起显示。相机和枪管按总装保存的姿态显示。当前导航仿真使用两路激光点云。

## 实车上装与导航模型

实车有大 yaw、小 yaw 和枪管的 pitch（俯仰）运动。yaw 描述左右转向，pitch 描述抬头和低头。总装中可见 `pitch电机支撑.SLDPRT` 和 `Pitch副铝件V3.0.SLDPRT`。这里沿用 RoboMaster 的运动名称，关节行程取决于本车机构。[RoboMaster AI 机器人 2020 标准版](https://www.robomaster.com/zh-CN/products/components/detail/2499) · [RoboMaster S1 官方规格](https://www.dji.com/robomaster-s1/downloads)

下面是 `robot_state_publisher` 从显示模型发布的车体 TF。Gazebo 中的枪管和前相机外壳合并在转台外观中，随大 yaw 转动，俯仰角保持 CAD 保存的姿态。

```text
base_link
└── chassis_link
    ├── wheel_1_link  左后
    ├── wheel_2_link  左前
    ├── wheel_3_link  右前
    ├── wheel_4_link  右后
    └── gimbal_yaw_link  大 yaw
        ├── small_yaw_link  空载小 yaw，相对大 yaw 转动
        ├── barrel_mesh_frame  枪管外观使用的网格坐标
        ├── odin1_lite_mount_link  Odin 外壳的 CAD 安装原点
        │   └── odin1_lite_link  TX 正前方的外侧面，仿真点云原点
        │       └── lidar_link  兼容旧坐标名
        └── mid360s_link
```

四个轮子的坐标轴分别画在各自的轮心。`barrel_mesh_frame` 使用上装网格的绘图原点。`坐标系 TF → Frames` 可分别开关它们。Odin1 Lite 默认显示 `odin1_lite_link` 扫描轴，需要看外壳参考时可勾选 `odin1_lite_mount_link`。

镜头局部 TF 为 `front_camera_link → front_camera_optical_frame`。两个坐标系共用镜头原点，光学坐标的 X 向图像右侧、Y 向下、Z 向前。启动时加 `camera_view:=true` 可同时打开局部视图，短粗轴表示本体，长细轴表示光学系。

从 `urdf/sentry.urdf.xacro` 看起。`chassis.xacro` 定义底盘和四个轮轴，`gimbal.xacro` 定义转台，`sensors.xacro` 把两个雷达固定到转台上。大 yaw 转动时，两台雷达随它转；大 yaw 保持不动，单独转小 yaw 时，两台雷达相对底盘的位置和方向都保持不变。小 yaw 的示意原点取在大 yaw 原点，只表达相对角度。整块上装 CAD 外观仍挂在大 yaw。

安装参数集中在 `config/frames.yaml`，`xyz` 以米为单位，`rpy` 是绕 X、Y、Z 的固定轴转角，单位为弧度。两台雷达的外壳位姿相对大 yaw。Odin 的右侧 TX 窗在显示网格的 (37, 15, 0) mm 处，正前面有一片 `Odin亚克力`，外表面在 X = 40.8 mm。仿真把出口放在这片护板外侧的 (41, 15, 0) mm，沿局部 +X 扫描。`/lidar/points` 与可见射线共用这个原点。此处用单一出口近似，不模拟透过亚克力的折射或衰减。[Odin1 Lite 硬件图](https://manifoldtechltd.github.io/wiki/odin_series/odin1lite/2.%20HW%20Description_.html)

Livox 使用总装中 `mid-360-asm（带范围）V2.001` 的安装参考，省去 CAD 里的视场显示体，S 型外壳用 65 × 65 × 60 mm 的圆角显示网格表示。两处扫描原点均为仿真名义值，实车测量中心相对零件原点的偏移还要按设备与安装标定。[Mid-360S 外形与参数](https://www.livoxtech.com/cn/mid-360s/specs)

RViz 和 Gazebo 默认加载 `meshes/navigation/` 里的 8 个 DAE 文件，长度单位为米。底盘按原总装外廓重画为圆角护板、平台和护栏，四只全向轮保留轮毂和两排滚子。轮心、轴向和轮子半径沿用 URDF。转台从 CAD 保留主要零件的外形，省去细小紧固件。平板保留边线，轮缘等曲面用平滑法线着色。Mid-360S 单独建模，底座保留四个圆角，上方使用连续的曲面扫描罩。底盘的碰撞盒、四轮的碰撞圆柱及刚体惯量单独定义。

日常改 URDF 或运行仿真直接使用随包提供的 DAE。要重新生成外观，在 `sentry_ws` 下运行下面这条命令，把路径换成自己的总装文件，并把配套零件留在原来的相对路径。生成工具需要 NumPy 和 SciPy。

```bash
python3 tools/smooth_navigation_visuals.py "/path/to/哨兵总装.SLDASM"
```

`tools/parametric_base.py` 画底盘、护栏和轮子。上装从总装显示缓存读取，Odin 从包内的原始 STL 读取，Mid-360S 按外壳截面生成。原装配中“零件2”和“零件3”缺少显示面。

只在 RViz 看模型时，在已加载工作空间的终端运行

```bash
ros2 launch sentry_description sentry_description.launch.py
```

要手动检查两个关节，启动带滑块的预览：

```bash
ros2 launch sentry_description sentry_description.launch.py joint_gui:=true
```

同时查看整车各轮和镜头坐标时运行

```bash
ros2 launch sentry_description sentry_description.launch.py joint_gui:=true camera_view:=true
```

在滑块中单独拖动 `wheel_2_joint`，左前轮坐标轴会随轮子转动。也可在另一个已加载工作空间的终端运行 `ros2 run tf2_ros tf2_echo chassis_link wheel_2_link` 查看该轮的变换。

拖动 `gimbal_yaw_joint` 可以看大 yaw 和两台雷达一起转。把它停在一个角度，再拖动 `small_yaw_joint`，只有代表小轴转角的黄色圆点绕转；两台雷达仍在原位。这个圆点只出现在 RViz 的滑块预览里。Gazebo 中小轴是被动关节，已有转台插件同时回报两轴的角度。

单独预览通过 `joint_state_publisher` 给轮子和转台提供零位。仿真总启动使用 Gazebo 发布的关节状态。激光点云的扫描参数在 `sentry_sim/urdf/gazebo/lidar.xacro`，同时看模型和两路点云使用 `ros2 launch sentry_bringup sentry_sim_teleop.launch.py`。

### 在 RViz 看俯仰角

独立预览会在车体旁显示角度表。灰线表示车体的水平方向，蓝色指针表示示例角度，白字给出度数。默认显示 0°，正数抬头，负数低头。显示范围是 −90° 到 +90°。表盘与枪管 CAD 外观分开，读数来自预览参数。

```bash
ros2 launch sentry_description sentry_description.launch.py pitch_preview_deg:=15.0
```

在另一个已加载工作空间的终端，可以直接改变显示值。例如从抬头 15° 切换到低头 10°：

```bash
ros2 param set /sentry_pitch_preview angle_deg -10.0
```

显示节点只发布 RViz 图形到 `/sentry_description/pitch_preview`。两台雷达继续使用大 yaw 上各自的安装坐标。
