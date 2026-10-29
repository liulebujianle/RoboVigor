# Per-wheel rotating axle TF

User corrected the interpretation explicitly: remove wheel_visuals.py and bottom-center aggregate TF. Each wheel, like radar/camera, is an independent frame at its axle center and rotates with the actual wheel. No per-roller TF flags.

- [x] Remove wheel_visuals.py source/install/cache and MarkerArray rendering/publishers/dependencies/configs.
- [x] Remove wheels_link fixed alias from Xacro, YAML and CAD extraction; keep four physical wheel_i_link frames public, omit roller links only from the display model.
- [x] Use standard RobotModel visualization. Static display URDF folds each roller's visual at its zero angle into its parent wheel, removing only roller links/joints. All118 meshes remain, wheel TF rotates the complete wheel visual; Gazebo still simulates112 passive roller joints physically.
- [x] RViz uses public TF, one frame per main wheel. Explicitly configure every public frame's checkbox (unspecified RViz TF frames default enabled). No aggregate wheel-center display, no MarkerArray wheel display, opaque model. Target view uses chassis_link.
- [x] Build/install and validate each wheel TF quaternion follows measured main joint rotation; public has4 wheel frames and no rollers/wheels_link; RobotModel has4x29 wheel mesh visuals and2 body meshes; camera/radar/gun frames retained. Refresh active RViz/launch and report exact package/files.
