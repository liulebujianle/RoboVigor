> 目录迁移后，模型位于 src/sentry_description，Gazebo 扩展位于 src/sentry_sim，
> 提取工具位于 sentinel_ws/tools。当前启动见工作空间 README。下文保留原验证历史。

# 用户机器人 URDF 接入检查

原文件：`/home/ethan/桌面/sentry.urdf`。

原样备份：`src/sentry_description/urdf/sentry_original.urdf`。

SHA-256：`6f1eb878ebc7b4c5ad11930a17d7eb0eb6f2757131af213653aa2a027b022dcc`。

包含 123 个 link、122 个 joint、781 处网格引用，共 195 个独立 STL。

所有 mesh 均引用 `package://sentry_description/meshes/`；当前还未找到这些配套文件。全部 link 都没有 collision 和 inertial，源文件也没有 Gazebo 插件。

接入状态：已从 `大小yaw哨兵/哨兵总装.SLDASM` 的真实显示缓存提取完整整车。
默认使用派生的 `src/sentry_description/urdf/sentry.urdf.xacro（平台）与 src/sentry_sim/urdf/sentry_sim.urdf.xacro（仿真）`，Gazebo 和 RViz
读取同一份解析安装资源后的 robot_description。原关节 URDF 保留作后续关节控制参考，
其未提供的 195 个独立 STL 不是当前运行入口的依赖。

装配解析：1161 个引用，782 个可见零件实例、125 个抑制引用、98 个隐藏引用，
其余为递归装配节点；没有缺失缓存，没有替换为零件默认配置。
MID-360 两个实例各移除 84 个扫描范围辅助三角形，硬件外形保留。
源可见实体边界约为 [-0.266604,-0.266604,-0.112600] 到 [0.266604,0.266604,0.383195] m。
网格简化采用 1 mm 顶点网格，输出 924552 个非退化三角形；不等于精确 B-rep 导出。
当前派生模型为保存的 CAD 姿态，云台与滚子关节不独立驱动；动力学仍是临时估计。

可复现提取脚本：`tools/import_sentry_cad.py`；读取器来源与 MIT 许可证
位于 `tools/vendor/sldprt/NOTICE.md`、`LICENSE`。
读取器上游：https://github.com/XRTC5/sldprt-export 。本地修正了目录序号不连续
导致只读出一个零件的问题，并统一实例路径匹配；回归测试位于 tools/tests。
原始 CAD 和桌面 URDF 均未改动。

工作空间根目录直接运行全仓 pytest 会在 Autoaim 包收集阶段因缺少 gxipy 失败；
这与当前场地仿真无关，未修改自瞄包。rm_arena 与 sentry_simulation 应各自在包目录测试。

原始参考 URDF 依赖清单（仅记录，不是当前运行入口的依赖）：

- `package://sentry_description/meshes/part_000.stl`
- `package://sentry_description/meshes/part_001.stl`
- `package://sentry_description/meshes/part_002.stl`
- `package://sentry_description/meshes/part_003.stl`
- `package://sentry_description/meshes/part_004.stl`
- `package://sentry_description/meshes/part_005.stl`
- `package://sentry_description/meshes/part_006.stl`
- `package://sentry_description/meshes/part_007.stl`
- `package://sentry_description/meshes/part_008.stl`
- `package://sentry_description/meshes/part_009.stl`
- `package://sentry_description/meshes/part_010.stl`
- `package://sentry_description/meshes/part_011.stl`
- `package://sentry_description/meshes/part_012.stl`
- `package://sentry_description/meshes/part_013.stl`
- `package://sentry_description/meshes/part_014.stl`
- `package://sentry_description/meshes/part_015.stl`
- `package://sentry_description/meshes/part_016.stl`
- `package://sentry_description/meshes/part_017.stl`
- `package://sentry_description/meshes/part_018.stl`
- `package://sentry_description/meshes/part_019.stl`
- `package://sentry_description/meshes/part_020.stl`
- `package://sentry_description/meshes/part_021.stl`
- `package://sentry_description/meshes/part_022.stl`
- `package://sentry_description/meshes/part_023.stl`
- `package://sentry_description/meshes/part_024.stl`
- `package://sentry_description/meshes/part_025.stl`
- `package://sentry_description/meshes/part_026.stl`
- `package://sentry_description/meshes/part_027.stl`
- `package://sentry_description/meshes/part_028.stl`
- `package://sentry_description/meshes/part_029.stl`
- `package://sentry_description/meshes/part_030.stl`
- `package://sentry_description/meshes/part_031.stl`
- `package://sentry_description/meshes/part_032.stl`
- `package://sentry_description/meshes/part_033.stl`
- `package://sentry_description/meshes/part_034.stl`
- `package://sentry_description/meshes/part_035.stl`
- `package://sentry_description/meshes/part_036.stl`
- `package://sentry_description/meshes/part_037.stl`
- `package://sentry_description/meshes/part_038.stl`
- `package://sentry_description/meshes/part_039.stl`
- `package://sentry_description/meshes/part_040.stl`
- `package://sentry_description/meshes/part_041.stl`
- `package://sentry_description/meshes/part_042.stl`
- `package://sentry_description/meshes/part_043.stl`
- `package://sentry_description/meshes/part_044.stl`
- `package://sentry_description/meshes/part_045.stl`
- `package://sentry_description/meshes/part_046.stl`
- `package://sentry_description/meshes/part_047.stl`
- `package://sentry_description/meshes/part_048.stl`
- `package://sentry_description/meshes/part_049.stl`
- `package://sentry_description/meshes/part_050.stl`
- `package://sentry_description/meshes/part_051.stl`
- `package://sentry_description/meshes/part_066.stl`
- `package://sentry_description/meshes/part_069.stl`
- `package://sentry_description/meshes/part_071.stl`
- `package://sentry_description/meshes/part_072.stl`
- `package://sentry_description/meshes/part_073.stl`
- `package://sentry_description/meshes/part_074.stl`
- `package://sentry_description/meshes/part_075.stl`
- `package://sentry_description/meshes/part_076.stl`
- `package://sentry_description/meshes/part_077.stl`
- `package://sentry_description/meshes/part_078.stl`
- `package://sentry_description/meshes/part_079.stl`
- `package://sentry_description/meshes/part_080.stl`
- `package://sentry_description/meshes/part_081.stl`
- `package://sentry_description/meshes/part_082.stl`
- `package://sentry_description/meshes/part_083.stl`
- `package://sentry_description/meshes/part_084.stl`
- `package://sentry_description/meshes/part_085.stl`
- `package://sentry_description/meshes/part_086.stl`
- `package://sentry_description/meshes/part_087.stl`
- `package://sentry_description/meshes/part_088.stl`
- `package://sentry_description/meshes/part_089.stl`
- `package://sentry_description/meshes/part_090.stl`
- `package://sentry_description/meshes/part_091.stl`
- `package://sentry_description/meshes/part_092.stl`
- `package://sentry_description/meshes/part_093.stl`
- `package://sentry_description/meshes/part_094.stl`
- `package://sentry_description/meshes/part_095.stl`
- `package://sentry_description/meshes/part_096.stl`
- `package://sentry_description/meshes/part_097.stl`
- `package://sentry_description/meshes/part_098.stl`
- `package://sentry_description/meshes/part_099.stl`
- `package://sentry_description/meshes/part_100.stl`
- `package://sentry_description/meshes/part_101.stl`
- `package://sentry_description/meshes/part_102.stl`
- `package://sentry_description/meshes/part_103.stl`
- `package://sentry_description/meshes/part_104.stl`
- `package://sentry_description/meshes/part_105.stl`
- `package://sentry_description/meshes/part_106.stl`
- `package://sentry_description/meshes/part_107.stl`
- `package://sentry_description/meshes/part_108.stl`
- `package://sentry_description/meshes/part_109.stl`
- `package://sentry_description/meshes/part_110.stl`
- `package://sentry_description/meshes/part_111.stl`
- `package://sentry_description/meshes/part_112.stl`
- `package://sentry_description/meshes/part_113.stl`
- `package://sentry_description/meshes/part_114.stl`
- `package://sentry_description/meshes/part_115.stl`
- `package://sentry_description/meshes/part_116.stl`
- `package://sentry_description/meshes/part_117.stl`
- `package://sentry_description/meshes/part_118.stl`
- `package://sentry_description/meshes/part_119.stl`
- `package://sentry_description/meshes/part_120.stl`
- `package://sentry_description/meshes/part_121.stl`
- `package://sentry_description/meshes/part_122.stl`
- `package://sentry_description/meshes/part_123.stl`
- `package://sentry_description/meshes/part_124.stl`
- `package://sentry_description/meshes/part_126.stl`
- `package://sentry_description/meshes/part_127.stl`
- `package://sentry_description/meshes/part_128.stl`
- `package://sentry_description/meshes/part_129.stl`
- `package://sentry_description/meshes/part_131.stl`
- `package://sentry_description/meshes/part_132.stl`
- `package://sentry_description/meshes/part_133.stl`
- `package://sentry_description/meshes/part_134.stl`
- `package://sentry_description/meshes/part_135.stl`
- `package://sentry_description/meshes/part_136.stl`
- `package://sentry_description/meshes/part_137.stl`
- `package://sentry_description/meshes/part_138.stl`
- `package://sentry_description/meshes/part_139.stl`
- `package://sentry_description/meshes/part_140.stl`
- `package://sentry_description/meshes/part_141.stl`
- `package://sentry_description/meshes/part_142.stl`
- `package://sentry_description/meshes/part_143.stl`
- `package://sentry_description/meshes/part_144.stl`
- `package://sentry_description/meshes/part_145.stl`
- `package://sentry_description/meshes/part_146.stl`
- `package://sentry_description/meshes/part_147.stl`
- `package://sentry_description/meshes/part_148.stl`
- `package://sentry_description/meshes/part_149.stl`
- `package://sentry_description/meshes/part_150.stl`
- `package://sentry_description/meshes/part_151.stl`
- `package://sentry_description/meshes/part_152.stl`
- `package://sentry_description/meshes/part_153.stl`
- `package://sentry_description/meshes/part_154.stl`
- `package://sentry_description/meshes/part_155.stl`
- `package://sentry_description/meshes/part_156.stl`
- `package://sentry_description/meshes/part_158.stl`
- `package://sentry_description/meshes/part_159.stl`
- `package://sentry_description/meshes/part_160.stl`
- `package://sentry_description/meshes/part_162.stl`
- `package://sentry_description/meshes/part_164.stl`
- `package://sentry_description/meshes/part_165.stl`
- `package://sentry_description/meshes/part_166.stl`
- `package://sentry_description/meshes/part_167.stl`
- `package://sentry_description/meshes/part_169.stl`
- `package://sentry_description/meshes/part_170.stl`
- `package://sentry_description/meshes/part_171.stl`
- `package://sentry_description/meshes/part_172.stl`
- `package://sentry_description/meshes/part_174.stl`
- `package://sentry_description/meshes/part_176.stl`
- `package://sentry_description/meshes/part_177.stl`
- `package://sentry_description/meshes/part_180.stl`
- `package://sentry_description/meshes/part_181.stl`
- `package://sentry_description/meshes/part_183.stl`
- `package://sentry_description/meshes/part_184.stl`
- `package://sentry_description/meshes/part_185.stl`
- `package://sentry_description/meshes/part_186.stl`
- `package://sentry_description/meshes/part_187.stl`
- `package://sentry_description/meshes/part_188.stl`
- `package://sentry_description/meshes/part_190.stl`
- `package://sentry_description/meshes/part_191.stl`
- `package://sentry_description/meshes/part_193.stl`
- `package://sentry_description/meshes/part_194.stl`
- `package://sentry_description/meshes/part_195.stl`
- `package://sentry_description/meshes/part_196.stl`
- `package://sentry_description/meshes/part_197.stl`
- `package://sentry_description/meshes/part_198.stl`
- `package://sentry_description/meshes/part_199.stl`
- `package://sentry_description/meshes/part_200.stl`
- `package://sentry_description/meshes/part_201.stl`
- `package://sentry_description/meshes/part_203.stl`
- `package://sentry_description/meshes/part_207.stl`
- `package://sentry_description/meshes/part_210.stl`
- `package://sentry_description/meshes/part_211.stl`
- `package://sentry_description/meshes/part_213.stl`
- `package://sentry_description/meshes/part_214.stl`
- `package://sentry_description/meshes/part_216.stl`
- `package://sentry_description/meshes/part_217.stl`
- `package://sentry_description/meshes/part_218.stl`
- `package://sentry_description/meshes/part_220.stl`
- `package://sentry_description/meshes/part_221.stl`
- `package://sentry_description/meshes/part_222.stl`
- `package://sentry_description/meshes/part_224.stl`
- `package://sentry_description/meshes/part_225.stl`
- `package://sentry_description/meshes/part_226.stl`
- `package://sentry_description/meshes/part_227.stl`
- `package://sentry_description/meshes/part_228.stl`
- `package://sentry_description/meshes/part_229.stl`
- `package://sentry_description/meshes/part_230.stl`
- `package://sentry_description/meshes/part_231.stl`
- `package://sentry_description/meshes/part_234.stl`
- `package://sentry_description/meshes/part_235.stl`
- `package://sentry_description/meshes/part_236.stl`

## 小陀螺控制更新

当前将源 CAD 的底盘装配和上方云台装配分别导出为 sentry_chassis.stl 与
sentry_gimbal.stl，合计 924552 个三角形，零角拼接外观与先前合并网格一致。
旧 sentry_simple.urdf 圆柱模型已从源码及安装目录移除；默认碰撞为底盘方盒。
主 yaw 轴 z=0.051 m 取自用户原 URDF；云台主 yaw 由 Gazebo 插件实际反向驱动，
其余小 yaw、pitch 和滚子仍保持 CAD 保存姿态。质量拆为 8 kg 底盘与 2 kg 云台，
惯量是均匀包络的临时估计。

输出 bounds_m 现在只统计真正写入的非退化三角形，边界为
[-0.267,-0.267,-0.113] 到 [0.267,0.267,0.336] m；source_bounds_m 单独保留
简化前的源边界。1 mm 顶点栅格会删除坍缩的小细节三角形，不能用源边界冒充输出实体边界。

完整控制入口为 sentry_simulation sim_teleop.launch.py：W/S/A/D 0.8 m/s、
Q/E 1.5 rad/s、X 开启 3 rad/s 小陀螺、C 或空格停止。


## 当前轮地动力学版本

原始装配是四轮斜置全向轮底盘。四根主轴均水平指向底盘中心，轮心位于
(±0.167317, ±0.167317, -0.036283) m。每轮 28 个滚子轴与主轴正交。
`tools/sentry_wheels.py` 用原 URDF 的 visual 变换唯一匹配 112 个原生 CAD 橡胶实例；
只拆出全向轮内部旋转总成，电机定子和悬挂支架仍固定。118 份可视网格在零角时
拼回原来的整车，三角形总数与原提取保持一致。

轮子连续关节使用有限电机力矩控制，被动滚子通过接触自由转动；底盘不直接设置
位置或速度。`/joint_states`、`/odom` 和 TF 发布物理引擎的实际状态。云台也改为
有限力矩电机。旧版理想 planar_move 和固定轮子结论仅代表历史版本。

碰撞与惯量是仿真近似：每个橡胶滚子用约 9.9 mm 半径球体拟合，轮毂用短圆柱，
底盘方盒离地；总质量约 10 kg。材料、质量和电机参数需要实车测量后标定。
实现依据：[Gazebo URDF 物理参数](https://get.gazebosim.org/tutorials/?tut=ros_urdf)、
[ODE 接触参数](https://classic.gazebosim.org/tutorials?tut=physics_params)。
实测记录见 validation/wheel_physics/README.md。
