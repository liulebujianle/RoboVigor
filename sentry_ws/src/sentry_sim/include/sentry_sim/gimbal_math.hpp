// Copyright 2026 RoboVigor contributors
// SPDX-License-Identifier: Apache-2.0
#ifndef SENTRY_SIM__GIMBAL_MATH_HPP_
#define SENTRY_SIM__GIMBAL_MATH_HPP_

#include <cmath>
#include <algorithm>

namespace sentry_sim
{
inline double hold_heading(double current, double parent_yaw, double heading)
{
  const double error = parent_yaw + current - heading;
  return current - std::atan2(std::sin(error), std::cos(error));
}

inline double wrap_angle(double angle)
{
  return std::atan2(std::sin(angle), std::cos(angle));
}

inline double bounded_torque(double torque, double limit)
{
  return std::isfinite(torque) ? std::clamp(torque, -limit, limit) : 0.0;
}
}  // namespace sentry_sim

#endif  // SENTRY_SIM__GIMBAL_MATH_HPP_
