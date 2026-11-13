#include <cassert>
#include <cmath>
#include <limits>
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

  // The actual barrel starts at the oblique CAD yaw/pitch, not joint zero.
  const double mount_yaw = -1.94780621162;
  const double mount_pitch = 0.316456434558;
  const sentry_sim::Direction forward{
    std::cos(mount_yaw) * std::cos(mount_pitch),
    std::sin(mount_yaw) * std::cos(mount_pitch), -std::sin(mount_pitch)};
  const sentry_sim::Direction yaw_axis{0.0, 0.0, 1.0};
  const sentry_sim::Direction pitch_axis{-std::sin(mount_yaw), std::cos(mount_yaw), 0.0};
  sentry_sim::ViewRates yaw_rates, pitch_rates, correction;
  assert(sentry_sim::view_rates(forward, yaw_axis, yaw_rates));
  assert(sentry_sim::view_rates(forward, pitch_axis, pitch_rates));
  assert(std::abs(yaw_rates.yaw - 1.0) < 1e-12);
  assert(std::abs(yaw_rates.pitch) < 1e-12);
  assert(std::abs(pitch_rates.yaw) < 1e-12);
  assert(std::abs(pitch_rates.pitch - 1.0) < 1e-12);
  // Target world zero must request +1.9478 yaw and -.31646 pitch.
  assert(sentry_sim::joint_correction(yaw_rates, pitch_rates,
    {-mount_yaw, -mount_pitch}, correction));
  assert(std::abs(correction.yaw + mount_yaw) < 1e-12);
  assert(std::abs(correction.pitch + mount_pitch) < 1e-12);
  // Chassis rotation is cancelled using measured world angular view rates.
  assert(sentry_sim::joint_correction(yaw_rates, pitch_rates, {2.0, 0.0}, correction));
  assert(std::abs(correction.yaw - 2.0) < 1e-12);
  assert(!sentry_sim::view_rates({0.0, 0.0, 1.0}, yaw_axis, yaw_rates));
  assert(!sentry_sim::joint_correction({1.0, 1.0}, {1.0, 1.0}, {1.0, 0.0}, correction));
  assert(sentry_sim::bounded_torque(std::numeric_limits<double>::quiet_NaN(), 5.0) == 0.0);
  assert(sentry_sim::bounded_torque(100.0, 5.0) == 5.0);
  assert(sentry_sim::bounded_torque(-100.0, 5.0) == -5.0);
}
