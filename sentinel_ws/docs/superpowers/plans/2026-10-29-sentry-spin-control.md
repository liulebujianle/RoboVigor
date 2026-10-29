# Sentry spin control implementation plan

> Use superpowers:executing-plans for inline execution, following the user's authorization to operate autonomously.

Goal: drive the actual CAD sentry in the field, faster, with X enabling chassis spin while the gimbal holds its world heading.
Architecture: retain gazebo_ros_planar_move; split cached CAD instances into chassis and upper-gimbal meshes. Add a continuous yaw joint and a small Gazebo C++ position/velocity stabilizer, publishing actual joint states and world gimbal pose. Python teleop streams motion and spin state through the existing watchdog.
Tech stack: ROS Humble, Gazebo Classic 11, C++17, Python3, existing native CAD importer.

- [x] Model: preserve visible CAD pose, split chassis/upper meshes at the native assembly boundary; joint pivot from original big_yaw_joint z=0.051. Replace cylinder collision with chassis box; remove obsolete simple cylinder model. Test combined visual bounds, finite mesh units, matching spawn clearance and joint topology.
- [x] Control: W/S/A/D 0.8 m/s, Q/E 1.5 rad/s; X enables 3 rad/s persistent spin, C disables spin, space stops all. Translation expires after 0.3 s; spin persists while the keyboard heartbeat exists. Watchdog stops motion and disables spin after 0.5 s loss. Clamp translation to 1.2 m/s and yaw to 4 rad/s. Test repeated X, C, space, stale input, nonfinite values and faster limits.
- [x] Stabilization: a gimbal_yaw_joint Gazebo plugin latches the current world heading when spin enables and counter-rotates the gimbal each simulation update. Publish joint_states and gimbal_pose; hold the relative joint angle when disabled, avoiding reset jumps. Test wrap handling and live world heading under spin.
- [x] Integration: sim_teleop includes the existing complete field/robot/Gazebo/RViz entry exactly once. Ensure library installation/runtime path and dependencies. Headless runtime test keyboard PTY W/S, X, translation while spinning, C, space and lost-keyboard stop, measuring actual odometry and gimbal_pose.
- [x] Verification/docs: package tests, native angle unit test, build, actual runtime evidence; document the single launch command and keys. Preserve original user URDF and source CAD.

Review focus: yaw wrap; repeated X cannot oscillate state; stop cannot leave spin latched; missing heartbeat stops both; CAD split preserves pose and all visible instances; no duplicate car or cylinder spawned; full field stays loaded.

Execution ledger: model topology/resource tests RED→GREEN; keyboard state/limits tests RED→GREEN;
C++ angle header test RED→GREEN; native build and all nine CTests passed. Real keyboard PTY
runtime verified motion, full-turn chassis spin, actual world gimbal stability and actual stop.
Final review finding fixed with RED→GREEN test: use /gimbal_pose for translation reference heading,
not independently sampled odom yaw plus joint angle. Output bounds metadata corrected to use only
emitted non-degenerate triangles; source bounds remain separately recorded. No deferred blockers.
