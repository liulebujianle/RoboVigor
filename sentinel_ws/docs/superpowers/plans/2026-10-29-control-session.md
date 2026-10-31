# Control startup and continuous motion

User requests stationary startup, X-only gyro activation, fixed world gimbal heading while spinning, straight continuous translation; also fix default Gazebo empty GUI / misplaced RViz robot.

Evidence: old gzserver PID22566 held11345 with missing model path; new server exited255. Five orphan keyboard nodes shared /teleop/* and fed one guard. Terminal movement expires .3s but initial desktop repeat delay can exceed it.

- [x] Gracefully stop identified stale server and keyboard nodes; preserve unrelated processes. Add server-exit whole-launch shutdown; regression observed fail then pass outside sandbox subprocess namespace.
- [x] Isolate raw input per launch using a unique control_session; default keyboard window is a directly managed ROS child so launch termination closes it. Keep all /cmd_vel output from one guard.
- [x] Add held-key model and Qt window: stationary/gyro-off startup; real press/release, diagonal normalization, idempotent X, C/space full stop; loss of focus stops. Retain terminal as optional CLI only. Input session consumed by guard and frontend.
- [x] Verify old raw topic publishers cannot move new robot; idle startup, sustained held W (including initial repeat interval), release, X gyro, fixed gimbal world heading, straight translation during spin, stop and launch cleanup. Do not change wheel torque/contact physics or idealize chassis motion.
- [x] Build/install relevant packages, run package/model/control checks, record actual default-port GUI and ROS/Gazebo state. Restart corrected full GUI at birth without sending movement commands.


Record: package tests pass; Python24 pass; GUI press/release and old-source isolation proved in actual Gazebo. Default UUID naming bug observed in real GUI run, regression RED→GREEN with digit-start mock. Straight trajectory with real braking remains within approx4.7cm/1m; cloud yaw error approx0.046deg. Additional lifecycle/client-close regression passes; historical validation data retained. No ideal chassis pose assignment introduced.
