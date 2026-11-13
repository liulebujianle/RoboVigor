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

struct Direction {double x; double y; double z;};
struct ViewRates {double yaw{0.0}; double pitch{0.0};};

// Derivative of world yaw and ROS pitch (-up) for a unit forward vector.
// Used for both joint-axis Jacobian columns and measured world angular rate.
inline bool view_rates(const Direction & forward, const Direction & omega, ViewRates & rates)
{
  const double horizontal = std::hypot(forward.x, forward.y);
  if (!std::isfinite(horizontal) || horizontal < 0.1) {
    return false;
  }
  const double dx = omega.y * forward.z - omega.z * forward.y;
  const double dy = omega.z * forward.x - omega.x * forward.z;
  const double dz = omega.x * forward.y - omega.y * forward.x;
  rates.yaw = (forward.x * dy - forward.y * dx) / (horizontal * horizontal);
  rates.pitch = -dz / horizontal;
  return std::isfinite(rates.yaw) && std::isfinite(rates.pitch);
}

// Solve the measured view Jacobian; no assumption that joint yaw/pitch equals
// world gun yaw/pitch. The CAD mount is oblique and the chassis may be tilted.
inline bool joint_correction(
  const ViewRates & yaw_axis, const ViewRates & pitch_axis,
  const ViewRates & view_error, ViewRates & joints)
{
  const double det = yaw_axis.yaw * pitch_axis.pitch - pitch_axis.yaw * yaw_axis.pitch;
  if (!std::isfinite(det) || std::abs(det) < 0.05) {
    return false;
  }
  joints.yaw = (pitch_axis.pitch * view_error.yaw - pitch_axis.yaw * view_error.pitch) / det;
  joints.pitch = (-yaw_axis.pitch * view_error.yaw + yaw_axis.yaw * view_error.pitch) / det;
  return std::isfinite(joints.yaw) && std::isfinite(joints.pitch);
}

inline double bounded_torque(double torque, double limit)
{
  return std::isfinite(torque) ? std::clamp(torque, -limit, limit) : 0.0;
}
}  // namespace sentry_sim

#endif  // SENTRY_SIM__GIMBAL_MATH_HPP_
