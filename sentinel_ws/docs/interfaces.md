# 当前话题接口

| 话题 | 类型 | 发布者 → 接收者 | 单位/说明 |
| --- | --- | --- | --- |
| /teleop/<control_session>/cmd_vel | geometry_msgs/Twist | keyboard → velocity guard | m/s、rad/s；普通模式车体参考，小陀螺模式按锁定云台航向解释 |
| /teleop/<control_session>/spin_mode | std_msgs/Bool | keyboard → guard | 心跳，超时停止 |
| /cmd_vel | geometry_msgs/Twist | guard → omni drive | 车体 x 前 y 左 z 逆时针；最终速度源唯一 |
| /spin_mode | std_msgs/Bool | guard → gimbal stabilizer | 保持世界航向开关 |
| /odom | nav_msgs/Odometry | omni drive → guard/调试 | Gazebo 真值，odom/world 重合；不是编码器定位 |
| /joint_states | sensor_msgs/JointState | wheel plugin 与 gimbal plugin → RSP | 两个发布者发布不同关节，rad、rad/s |
| /gimbal_pose | geometry_msgs/PoseStamped | gimbal plugin → guard | world 中的实际云台姿态 |
| /robot_description | std_msgs/String | robot_state_publisher → RViz | 四轮独立TF/显示URDF |
| /arena_marker | visualization_msgs/Marker | rm_arena → RViz | world、米、嵌入材质；Reliable/TransientLocal depth=1 |

命令使用小队列，保护用单调墙钟，仿真状态使用 /clock 时间戳。暂无 Nav2 Action/自定义 Service/真机协议。

control_session 由每次启动生成 UUID，guard 与当前键盘窗口使用同一前缀；旧通道输入不被接收。

/sentry_description/robot_description_physics 为 std_msgs/String，完整Gazebo物理模型，
由physics_description_publisher保留发布并供spawn_entity读取。两种描述的118个可视网格相同；
公开模型只将滚子外观归入对应车轮，四个主轮和云台使用实际joint_states。
