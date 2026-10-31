# Compact public wheel TF and CAD component frames

Goal: one wheel-group frame on public /tf, explicit chassis/lidar/camera/gun frames, preserve Gazebo physics and RViz wheel animation. Location: sentry_description. Default interpretation stated to user; optional async alternative was RViz-only hiding.

Constraints: preserve all 117 actuated joints/118 visuals and torque/contact values; do not merge physical wheel axes. Two radar units and one MV-CS004 camera exist in actual CAD. Frame origins are mechanical CAD references, not calibrated sensor optical centers. Current small-yaw/pitch are fixed at saved CAD pose.

- [x] Recover frames from current native part instance matrices (not older original URDF gimbal pose); config/frames.yaml records provenance/conventions. wheels_link = four axle centroid; lidar/link axes documented; camera optical conventional axes; gun axis from speed module, gun origin from visible CAD projectile, muzzle along that axis at module exit plane.
- [x] Add sensors.xacro fixed reference links and regeneration support; maintain physical model semantic invariance excluding explicit massless reference links.
- [x] Write failing TF routing tests; implement private full RSP bus and public filtered bus. Public only wheels_link, no wheel_N/roller_N links; relay public odometry/world transforms to full visualization bus without loops. Static snapshots must serve late subscribers.
- [x] Configure official simulation RViz to use full visualization bus and show only public named axes. rm_arena standalone retains normal public TF defaults. Keep one RSP and one owner per public edge.
- [x] Build/install, unit checks, actual isolated runtime: compact public tree and complete internal wheel transforms; sensor world transforms and gimbal tracking; wheel animation states/physics unchanged. Record files/package/launch command and approximation limits.

Rulings: internal wheel/roller frames remain on a separate display bus, as four independent physical axes cannot share one rotating frame. CAD sensor/body axes are explicitly mechanical conventions; no claim of driver calibration or real sensor messages.

Execution: Python31 passed; all five package tests passed; actual late-join TF snapshot/root connectivity verified. Public11 children vs full127; physical wheel angle changed; camera/gun/lidar headings stable during gyro. Default GUI launch PID39335 stationary near (1.25,6.75), public wheelgroup only, no startup errors. Record docs/validation/public_frames.
