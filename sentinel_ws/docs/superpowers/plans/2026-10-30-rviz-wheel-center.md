# RViz wheel center only

Problem: public TF was filtered, but RViz subscribed to the private complete bus for RobotModel animation. Adding/enabling a TF display still exposes 116 internal wheel/roller frames.

Goal: every standard RViz TF display, including a newly added All Enabled display, sees only wheels_link for the wheel assembly. Preserve physical joints and actual wheel animation.

- [ ] Add a compact visual description with internal wheel/roller links removed; preserve all chassis/gimbal/component reference links. Keep full physics URDF unchanged.
- [ ] Render the 116 actual wheel/roller mesh visuals as MarkerArray, with poses from measured private full TF, anchored only to wheels_link. Test visual-origin rotation/translation and mesh scales.
- [ ] Restore RViz to public /tf and /tf_static and compact description; add Wheel Visuals MarkerArray display. New TF displays cannot access the private wheel tree. Existing private full TF remains for diagnostics/marker pose lookup.
- [ ] Build/install, regression and actual runtime verify same visual count (2 RobotModel meshes +116 markers), rotating wheel poses, compact public TF and no missing model TF. Restart the active owned launch/config after verification.
