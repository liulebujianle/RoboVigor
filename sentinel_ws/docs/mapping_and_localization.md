# 建图与定位状态

当前只加载 Gazebo 三维场地和 RViz 场地 Marker，没有生成 Nav2 map.yaml/map.pgm 或 prior.pcd。
不将 DAE/STL 当作占据栅格地图。sentry_maps 与导航/建图后端在实际地图制作阶段建立。
LIO、先验地图匹配和重定位均未接入；不发布伪造 map→odom。
后续按场地 rmul_2027 保持 world、地图、区域与航点坐标一致。
