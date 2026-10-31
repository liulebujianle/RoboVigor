# Wheel-driven physical sentry

User requested wheel rotation obeying physical laws. Continue autonomous implementation in the current workspace with TDD and final independent review.

- [x] Recover original wheel axes and passive roller axes from the supplied URDF; identify actual rotating hub subassemblies from CAD so motor stators and suspension brackets remain fixed. Preserve all visual instances at zero joint angle.
- [x] Generate four driven wheel joints and 112 passive rubber-roller joints. Use small sphere contact surrogates fitted to each near-spherical rubber roller; preserve measured axle geometry. Move the chassis collision above the wheel-ground contact plane. All masses/inertias positive; provisional total mass approximately 10 kg.
- [x] Replace planar_move with torque-limited wheel velocity PI control, using wheel geometry inverse kinematics. Publish actual wheel/roller joint states and ground-truth simulation odometry/TF. Never set chassis pose or velocity to create locomotion.
- [x] Replace ideal gimbal position/velocity assignment with bounded motor torque feedback; preserve X spin and world-heading hold.
- [x] Test axle handedness and rolling constraints; actual grounded forward/back/lateral/spin, wheel/roller motion and slip; actual braking; airborne spinning wheels must not translate the vehicle by a direct velocity assignment. Verify field stays loaded.
- [x] Build, full package checks, independent review, record physical approximations and final command. Keep W/S/A/D, X/C/space and watchdog behavior.

Native evidence: four inward radial horizontal axles at (+/-0.167317,+/-0.167317,-0.036283) m, 28 rollers per wheel, roller axes orthogonal to main axle. This CAD is an X-drive omni arrangement. Rubber roller radius approximately 9.9 mm and axial length 18.5 mm. Mass, stiffness, damping and friction are provisional because no calibrated measurements were supplied.
