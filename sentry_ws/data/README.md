# 本机数据

录包放 `bags/`，建图中间结果放 `mapping/`，用到时再创建，默认不提交。
整理好的地图放到 `src/sentry_maps/maps/`。固定场地资源从 `sentry_map` 的安装目录读取。

本目录通过 `COLCON_IGNORE` 排除，不参与 colcon 包扫描。
