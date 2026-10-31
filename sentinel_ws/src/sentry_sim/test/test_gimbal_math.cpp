#include <cassert>
#include <cmath>
#include "sentry_sim/gimbal_math.hpp"

int main()
{
  assert(std::abs(sentry_sim::hold_heading(0.0, 1.2, 0.0) + 1.2) < 1e-12);
  double position = 0.0;
  for (int i = 0; i < 3000; ++i) {
    const double chassis_yaw = std::atan2(std::sin(i * 0.01), std::cos(i * 0.01));
    const double next = sentry_sim::hold_heading(position, chassis_yaw, 0.7);
    const double error = std::atan2(
      std::sin(chassis_yaw + next - 0.7),
      std::cos(chassis_yaw + next - 0.7));
    assert(std::abs(error) < 1e-10);
    assert(std::abs(next - position) < 0.71);
    position = next;
  }
}
