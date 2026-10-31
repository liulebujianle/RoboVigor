# Lightweight X-drive omni sentry

User clarification: preserve the omnidirectional layout, measure the new native assembly at `/home/ethan/桌面/大小yaw哨兵(2)/大小yaw哨兵`, replace detailed wheel constructions with ordinary cylinders, and reduce URDF runtime load.

Measured: driven radius 76.1 mm (roller envelope), assembly radial mesh maximum 76.444 mm, axial width 39.798 mm, axial visual-center offset -1.5004 mm. Four original centers/axes recovered using the saved CAD instance transforms and original URDF correspondence. Evidence stored in description/config/wheel_dimensions.json. Preserve original axle centers and 45-degree axes.

Four cylindrical visuals/collisions replace all hub/roller meshes and 112 passive bodies. Five moving joints remain including gimbal. Anisotropic friction (low along axle, high in rolling direction) approximates the transverse free motion of an omni wheel; it is not a conventional solid tire's isotropic contact model. Retain body/sensor frames and torque-driven contact dynamics, standard RSP and public TF. Restore omni keyboard mapping and world-heading spin control.

Separate *_low.stl visuals use 4 mm vertex clustering, removing collapsed/duplicate faces. Keep original CAD meshes and source assembly untouched; maximum displacement 3.464 mm, no collision geometry uses triangles. 689748 original body/gimbal triangles reduce to 176015. CAD detail is approximate, sensors remain nominal extrinsics.

Keep launch script LF shebang, retained map QoS and default field overview. Verify geometry/unit tests and actual simulated forward/reverse/lateral/yaw motion, braking and gimbal hold. Refresh complete Gazebo/RViz launch.
