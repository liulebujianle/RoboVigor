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
  // Contact velocity cancels body velocity along the driven rolling direction.
  return (ay * (vx - wz * y) - ax * (vy + wz * x)) / radius;
}
}  // namespace sentry_sim
#endif  // SENTRY_SIM__OMNI_KINEMATICS_HPP_
