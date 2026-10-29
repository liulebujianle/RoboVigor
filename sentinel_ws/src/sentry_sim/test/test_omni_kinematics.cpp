// Copyright 2026 RoboVigor contributors
// SPDX-License-Identifier: Apache-2.0
#include <cmath>
#include "sentry_sim/omni_kinematics.hpp"

int main()
{
  const double s = std::sqrt(0.5), a = 0.16731710127, radius = 0.0761;
  const double positions[4][2] = {{-a, a}, {a, a}, {a, -a}, {-a, -a}};
  const double velocities[4][3] = {{0.8, 0, 0}, {0, 0.8, 0}, {0, 0, 3}, {0.3, -0.2, 1.5}};
  for (const auto & velocity : velocities) {
    for (const auto & position : positions) {
      const double ax = -std::copysign(s, position[0]);
      const double ay = -std::copysign(s, position[1]);
      const double rate = sentry_sim::wheel_rate(
        ax, ay, position[0], position[1], radius,
        velocity[0], velocity[1], velocity[2]);
      // Rigid-body contact velocity plus rotating-wheel velocity has no
      // component along the driven rolling direction (ay, -ax).
      const double contact_x = velocity[0] - velocity[2] * position[1] - radius * rate * ay;
      const double contact_y = velocity[1] + velocity[2] * position[0] + radius * rate * ax;
      if (std::abs(contact_x * ay - contact_y * ax) > 1e-12) {
        return 1;
      }
    }
  }
  return 0;
}
