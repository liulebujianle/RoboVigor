> Superseded: user explicitly retained the X-drive omni layout and requested simple cylindrical wheels with lower simulation load. Differential steering was an incorrect interpretation. See 2026-10-31-lightweight-omni.md.

# Ordinary wheels and differential steering

User requests replacing mecanum/omni wheels because the car cannot drive normally. The existing simplified model removed all passive rollers but retained four diagonal axles, causing conflicting rolling constraints.

Implement four ordinary cylindrical tires (radius .0761 m, width .04 m), parallel Y axles at the same longitudinal centers and widened lateral centers ±.195 m. Keep four wheel frames, chassis CAD, sensors and gimbal. Drive with finite joint torque using vx/wz differential kinematics. Discard unsupported vy at the drive boundary. Configure wheel contacts for skid steering with finite lateral slip. W/S forward/reverse; A/D and Q/E turn; X stationary spin, C/space stop. Conventional wheels cannot translate sideways or sustain straight-world translation while the chassis spins continuously.

Retain the preceding LF script and retained-map QoS fixes, and make the default RViz view a field overview. Validate actual forward/reverse/yaw motion and wheel joint rotation using Gazebo odometry, then refresh the full GUI launch.
