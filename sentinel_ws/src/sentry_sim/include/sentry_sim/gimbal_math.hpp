// Copyright 2026 RoboVigor contributors
// SPDX-License-Identifier: Apache-2.0
#ifndef SENTRY_SIM__GIMBAL_MATH_HPP_
#define SENTRY_SIM__GIMBAL_MATH_HPP_

#include <cmath>

namespace sentry_sim
{
inline double hold_heading(double current, double parent_yaw, double heading)
{
  const double error = parent_yaw + current - heading;
  return current - std::atan2(std::sin(error), std::cos(error));
}
}  // namespace sentry_sim

#endif  // SENTRY_SIM__GIMBAL_MATH_HPP_
