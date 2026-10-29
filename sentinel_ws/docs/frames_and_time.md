# TF 与时间：四个独立轮轴

当前按用户明确要求：每个轮子在实际轮轴中心有一个独立 TF，跟随该轮子旋转；
没有底盘底部的 wheels_link 聚合坐标，没有每个滚子的独立 TF。

```text
world
└── odom
    └── base_link
        └── chassis_link
            ├── wheel_1_link    # 真实 wheel_1_joint 角度
            ├── wheel_2_link    # 真实 wheel_2_joint 角度
            ├── wheel_3_link    # 真实 wheel_3_joint 角度
            ├── wheel_4_link    # 真实 wheel_4_joint 角度
            └── gimbal_yaw_link
                ├── lidar_link
                ├── lidar_aux_link
                ├── camera_link
                │   └── camera_optical_frame
                └── gun_link
                    └── muzzle_link
```

## 文件归属

所有机器人描述维护在 `sentry_description` 包：
- `urdf/chassis.xacro`：四个实际轮轴的 link、joint、origin、axis。
- `urdf/gimbal.xacro`：实际主云台关节。
- `urdf/sensors.xacro`、`config/frames.yaml`：雷达、相机、枪管和枪口的CAD名义参考。
- `launch/description.launch.py`：标准可视/TF描述生成及唯一 robot_state_publisher 启动。
- `scripts/description_publisher.py`：向 Gazebo 保留完整物理描述。

## 单一公开 TF 与模型

world→odom：spawn_robot.launch.py 的唯一静态发布者。
odom→base_link：Gazebo 轮地动力学插件的实际姿态。
车体内部与四个轮轴：唯一原生 robot_state_publisher，使用实际 /joint_states。
只有 wheel_1_link～wheel_4_link 作为车轮 TF；其中心、轴线、关节角与物理模型一致。
不使用私有TF转发、不使用MarkerArray动画、不使用wheel_visuals.py。

模型分为两个明确话题：
- `/robot_description`：RViz 和原生 TF 使用的描述，5个活动关节（4轮+主云台）。
  每个车轮包含轮毂与28个滚子的可视/碰撞几何，共118个CAD网格；这些细节不单独成为TF。
- `/sentry_description/robot_description_physics`：Gazebo生成使用的完整117活动关节描述，
  仍有112个真实被动滚子及全部惯量、接触和力矩插件。

RViz用标准RobotModel和普通 `/tf`、`/tf_static`，四轮各自刚性外观随实测轮角旋转。
被动滚子的独立物理旋转仍在Gazebo中计算；RViz把滚子几何归属对应车轮，不发布滚子TF。
默认TF显示显式选中四个轮轴、雷达、相机和枪管；不显示根坐标的底盘底部轴标志。
手动增加TF显示也只会取得这棵精简原生树，不会出现112个滚子帧。

## 安装位姿与限制

四个轮轴中心相对chassis_link为 (±0.167317,±0.167317,-0.036283)m，轴线保持原CAD/URDF定义。
雷达、相机和枪管从当前保存的原生CAD实例矩阵恢复，单位米/弧度。
camera_optical_frame使用x右/y下/z前，原点仍为名义CAD相机原点，尚未标定真实光心。
枪口是发射轴与测速模块前机械平面的名义交点。小yaw/pitch当前固定在CAD保存姿态。
这些不是实车标定外参，也没有生成实际传感器数据。CAD重新提取会刷新名义安装配置。

RSP与RViz使用仿真时间；键盘超时使用单调墙钟。map→odom和Nav2定位尚未接入。
