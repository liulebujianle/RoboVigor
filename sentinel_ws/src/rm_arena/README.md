# rm_arena

ROS 2 Humble / Gazebo Classic 11 的 RMUL 2027 场地包。场地以官方 STEP
（`RMUL2027_3V3_V1.0.0.stp`）为唯一源，启动时由 launch 现场生成，world、网格、
贴图和 RViz 配置随包安装，不需要 `gazebo_arena`，也不需要设置 `ROBOVIGOR_ROOT`。

## 场地坐标与尺寸

- 内场 **12 × 8 m**，西南角为原点，X 向东、Y 向北、Z 向上，单位米。
- 围挡外扩 **0.3 m**（外轮廓 12.6 × 8.6 m），围挡顶高 **0.42 m**。
- 地台底面在 **z = -0.1 m**，比赛地面正好 **z = 0**。
- 场内凸起按 STEP 实测：两块 0.40 m 高地、0.27 m 台阶、0.20 m 平台。

## 用 launch 启动（STEP 自动转换）

```bash
ros2 launch rm_arena step_field.launch.py step:=/path/RMUL2027_3V3_V1.0.0.stp
```

流程是两段式的：先跑 `step_to_field` 把 STEP 转成 DAE + 碰撞盒 + `model.sdf`，
**转换成功才**拉起 gzserver/gzclient 和 RViz；失败会说明缺什么依赖并结束 launch。

| 参数 | 默认 | 说明 |
|---|---|---|
| `step` | 空 | 官方 STEP 路径；留空则直接用包里已有场地 |
| `convert` | `true` | 每次启动都重新生成 |
| `out` | 安装目录的 `models/rmul_2027` | 生成到别处就改这里（只影响 Gazebo 里的场地） |
| `tol` | `1.0` | 三角化弦差，mm |
| `gazebo` / `gui` / `rviz` | `true` | 三个开关，与 `simulation.launch.py` 一致 |

整个转换需要 `cascadio`（自带 OpenCASCADE）和 `trimesh`：

```bash
python3 -m pip install --user cascadio trimesh
```

只想重新生成资产、不启动 Gazebo：

```bash
ros2 run rm_arena step_to_field --step /path/RMUL2027_3V3_V1.0.0.stp \
    --out ~/sentinel_ws/src/rm_arena/models/rmul_2027
```

## 不用转换，直接看场地

```bash
ros2 launch rm_arena simulation.launch.py                  # Gazebo + RViz
ros2 launch rm_arena simulation.launch.py rviz:=false      # 只开 Gazebo
ros2 launch rm_arena simulation.launch.py gazebo:=false    # 只开 RViz
```

只用包里已装好的资产。整机仿真在 `sentry_sim` / `sentry_bringup` 里组合：

```bash
ros2 launch sentry_bringup sim_teleop.launch.py
```

## 资产

| 文件 | 说明 |
|---|---|
| `models/rmul_2027/meshes/field.dae` | 视觉网格，3811 个三角面，材质沿用改造前的配色 |
| `models/rmul_2027/materials/textures/official_top.png` | 场地俯视贴图，UV = (x/12, y/8) |
| `models/rmul_2027/model.sdf` | `<static>` 模型：1 个 visual + 29 个封闭碰撞盒 |
| `models/rmul_2027/meshes/field_stats.json` | 生成器产出的尺寸/碰撞清单，可追溯 |
| `rm_arena/step_to_field.py` | STEP → 上面三样的转换器 |

碰撞体是**按实测高度生成的封闭盒**（地台 1 块、围挡 4 条 + 压边、场内凸起若干），
不是把三角面当碰撞体，ODE 下更稳，也不会被车体穿过。

## 验证

```bash
colcon test --packages-select rm_arena --event-handlers console_direct+
colcon test-result --verbose
```

资源测试会把 setuptools 的真实数据文件清单复制到临时安装目录，检查
world → model → mesh → texture 引用是否完整；`test_field_model.py` 再核对
场地范围、地面高度、围挡 0.42 m 与碰撞盒数量。图形界面外观、机器人全地形运动
和导航效果仍需在实际运行环境验收。

本包代码声明 Apache-2.0；官方场地几何、纹理和标识的权利归原权利人，
不因代码许可证而重新授权，见 [来源说明](docs/SOURCE_NOTICE.txt)。
