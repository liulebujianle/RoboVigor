// Copyright 2026 RoboVigor contributors
// SPDX-License-Identifier: Apache-2.0
#include <cmath>
#include <limits>
#include "sentry_sim/gimbal_math.hpp"

int main()
{
  if (std::abs(sentry_sim::hold_heading(0.0, 1.2, 0.0) + 1.2) >= 1e-12) {
    return 1;
  }
  double position = 0.0;
  for (int i = 0; i < 3000; ++i) {
    const double chassis_yaw = std::atan2(std::sin(i * 0.01), std::cos(i * 0.01));
    const double next = sentry_sim::hold_heading(position, chassis_yaw, 0.7);
    const double error = std::atan2(
      std::sin(chassis_yaw + next - 0.7),
      std::cos(chassis_yaw + next - 0.7));
    if (!std::isfinite(error) || std::abs(error) >= 1e-10 ||
      std::abs(next - position) >= 0.71)
    {
      return 2;
    }
    position = next;
  }

  if (sentry_sim::bounded_torque(std::numeric_limits<double>::quiet_NaN(), 5.0) != 0.0 ||
    sentry_sim::bounded_torque(100.0, 5.0) != 5.0 ||
    sentry_sim::bounded_torque(-100.0, 5.0) != -5.0)
  {
    return 3;
  }
  return 0;
}
