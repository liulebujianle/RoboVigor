// Copyright 2026 RoboVigor contributors
// SPDX-License-Identifier: Apache-2.0
#ifndef SENTRY_SIM__OMNI_KINEMATICS_HPP_
#define SENTRY_SIM__OMNI_KINEMATICS_HPP_
namespace sentry_sim
{
inline double wheel_rate(
  double ax, double ay, double x, double y, double radius,
  double vx, double vy, double wz)
{
  // 轮面接触速度抵消车体沿驱动滚动方向的速度。
  return (ay * (vx - wz * y) - ax * (vy + wz * x)) / radius;
}
}  // namespace sentry_sim
#endif  // SENTRY_SIM__OMNI_KINEMATICS_HPP_
