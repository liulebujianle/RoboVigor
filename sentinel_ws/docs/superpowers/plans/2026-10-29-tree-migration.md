# Target tree migration implementation plan

Goal: migrate existing runtime code to the package responsibilities and names in /home/ethan/桌面/算法导航提示词.md, retaining working CAD, wheel physics, gimbal spin, Gazebo field and RViz.
Architecture: description owns platform Xacro and CAD assets; sim owns Gazebo additions and C++ plugins; motion owns keyboard/guard; bringup composes them; rm_arena owns field assets. Future navigation/hardware modules remain explicitly unimplemented pending user scope reply.
Tech stack: installed ROS 2 Humble, Gazebo Classic 11, ament_cmake, Python launch, Xacro.

Constraints: preserve Autoaim; no invented map/sensor/navigation data; all launch paths resolve installed package resources; no source-tree runtime imports; preserve actual mesh topology and physical parameters. Existing working tree is shared and dirty, so migrate in place and keep old generated package prefixes in /tmp rather than resetting/deleting work.
Review focus: same robot_description in Gazebo/RViz; no duplicate TF/guard; installed meshes/plugins resolve; standalone model doesn't require Gazebo; fresh environment selects new packages; CAD importer reproduces new layout.

- [x] Add migration regression checking package boundaries, Xacro composition and numerical equivalence of current robot model; observe failure before moving code.
- [x] Split sentry_simulation into sentry_description, sentry_sim, sentry_motion, sentry_bringup; add correct dependencies/install rules. Split platform Xacro and Gazebo extension, share one published description. Keep physics numeric values unchanged.
- [x] Add explicit rm_arena world/preview entries and empty debug world; preserve current textured field assets.
- [x] Move project tools and docs beneath sentinel_ws; archive superseded external arena resources beneath data; add build/sim scripts, architecture/interfaces/TF/status docs and actual tree. Update CAD importer and editor paths.
- [x] Build/install new packages; run resource, articulation, control and launch checks; run actual installed unified-launch keyboard+physics smoke in isolated ROS/Gazebo domain. Independent final review, fix material findings, record command and outstanding unimplemented modules.

Decision: implement existing functionality only unless user chooses full future scaffold; target document explicitly forbids creating every planned package at once. Preserve additional real CAD meshes and textured rm_arena/models (required working assets) under their correct responsibility rather than replacing them with fictitious tree example STL.


Execution record: model/control/layout Python 17 passed; all five packages build/test passed; installed launch/model/config files equal source. Actual unified-launch keyboard+Gazebo smoke passed (metrics in docs/validation/tree_migration). Fresh review dependency finding reproduced by a failing test, fixed and rechecked green. Source-only documentation history retained and clearly marked. No commits or destructive cleanup of unrelated changes performed.
