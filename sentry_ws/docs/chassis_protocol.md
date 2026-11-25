# 底盘通信

`/cmd_vel` 目前只发给 Gazebo 底盘插件，实车的 `sentry_chassis_bridge` 还是包骨架。

接电控前需要确认报文格式、单位、坐标方向、CRC、发送周期、反馈字段和下位机超时停车。裁判通信单独放在 `sentry_referee_bridge`，接线方式和对应赛季协议也还没确定。