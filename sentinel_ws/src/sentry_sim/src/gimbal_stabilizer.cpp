// Copyright 2026 RoboVigor contributors
// SPDX-License-Identifier: Apache-2.0
#include <algorithm>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <functional>
#include <memory>
#include <mutex>

#include <gazebo/common/Events.hh>
#include <gazebo/common/Plugin.hh>
#include <gazebo/physics/physics.hh>
#include <gazebo_ros/node.hpp>
#include <geometry_msgs/msg/pose_stamped.hpp>
#include <geometry_msgs/msg/vector3_stamped.hpp>
#include <sensor_msgs/msg/joint_state.hpp>
#include <std_msgs/msg/bool.hpp>

#include "sentry_sim/gimbal_math.hpp"

namespace sentry_sim
{
// Finite, bounded joint motor forces only; never assigns model/link poses.
class GimbalStabilizer : public gazebo::ModelPlugin
{
public:
  void Load(gazebo::physics::ModelPtr model, sdf::ElementPtr sdf) override
  {
    model_ = model;
    node_ = gazebo_ros::Node::Get(sdf);
    joint_ = model_->GetJoint("gimbal_yaw_joint");
    pitch_joint_ = model_->GetJoint("gimbal_pitch_joint");
    if (!joint_ || !pitch_joint_) {
      RCLCPP_ERROR(node_->get_logger(), "Missing gimbal yaw/pitch joint in the robot model");
      return;
    }
    gimbal_ = joint_->GetChild();
    pitch_link_ = pitch_joint_->GetChild();
    camera_offset_ = sdf->Get<ignition::math::Vector3d>(
      "fps_camera_offset", ignition::math::Vector3d(0.16416425837, 0, 0)).first;
    relative_target_ = joint_->Position(0);
    pitch_target_ = pitch_joint_->Position(0);
    command_ = node_->create_subscription<std_msgs::msg::Bool>(
      "/spin_mode", 1, [this](const std_msgs::msg::Bool::SharedPtr message) {
        requested_.store(message->data);
      });
    look_ = node_->create_subscription<geometry_msgs::msg::Vector3Stamped>(
      "/fps/look", rclcpp::QoS(1),
      [this](const geometry_msgs::msg::Vector3Stamped::SharedPtr message) {
        const auto & v = message->vector;
        if (message->header.frame_id != "world" || !std::isfinite(v.x) ||
          !std::isfinite(v.y) || !std::isfinite(v.z))
        {
          return;
        }
        std::lock_guard<std::mutex> lock(look_mutex_);
        look_yaw_ = wrap_angle(v.x);
        look_pitch_ = std::clamp(v.y, -1.0471975511965976, 1.0471975511965976);
        // ROS/sim time can pause or jump: expiry always uses monotonic receive time.
        last_look_ = std::chrono::steady_clock::now();
        have_look_ = true;
      });
    states_ = node_->create_publisher<sensor_msgs::msg::JointState>("/joint_states", 10);
    pose_ = node_->create_publisher<geometry_msgs::msg::PoseStamped>("/gimbal_pose", 10);
    view_ = node_->create_publisher<geometry_msgs::msg::PoseStamped>("/fps/view_pose", 10);
    update_ = gazebo::event::Events::ConnectWorldUpdateBegin(
      std::bind(&GimbalStabilizer::Update, this, std::placeholders::_1));
    RCLCPP_INFO(node_->get_logger(), "Gimbal motors ready on /spin_mode and /fps/look");
  }

  void Reset() override
  {
    requested_.store(false);
    active_ = false;
    fps_active_ = false;
    {
      std::lock_guard<std::mutex> lock(look_mutex_);
      have_look_ = false;
    }
    last_publish_ = gazebo::common::Time::Zero;
    if (joint_ && pitch_joint_) {
      relative_target_ = joint_->Position(0);
      pitch_target_ = pitch_joint_->Position(0);
    }
  }

private:
  static Direction direction(const ignition::math::Vector3d & vector)
  {
    return {vector.X(), vector.Y(), vector.Z()};
  }

  // Camera +X (barrel direction), not the optical-frame +Z quaternion. This
  // same physical-link offset is used by the Gazebo camera sensor in xacro.
  ignition::math::Pose3d CameraPose() const
  {
    const auto actual = pitch_link_->WorldPose();
    return ignition::math::Pose3d(
      actual.Pos() + actual.Rot().RotateVector(camera_offset_), actual.Rot());
  }

  double GravityCompensation() const
  {
    const auto lever = pitch_link_->WorldCoGPose().Pos() - pitch_joint_->Anchor(0);
    const auto gravity_force = model_->GetWorld()->Gravity() * pitch_link_->GetInertial()->Mass();
    return -lever.Cross(gravity_force).Dot(pitch_joint_->GlobalAxis(0));
  }

  void ApplyLook(double yaw, double pitch)
  {
    const auto forward = CameraPose().Rot().RotateVector(ignition::math::Vector3d::UnitX);
    ViewRates yaw_axis, pitch_axis, actual_rate, error, correction, damping;
    const bool valid = view_rates(direction(forward), direction(joint_->GlobalAxis(0)), yaw_axis) &&
      view_rates(direction(forward), direction(pitch_joint_->GlobalAxis(0)), pitch_axis) &&
      view_rates(direction(forward), direction(pitch_link_->WorldAngularVel()), actual_rate);
    error.yaw = wrap_angle(yaw - std::atan2(forward.Y(), forward.X()));
    error.pitch = pitch - std::atan2(-forward.Z(), std::hypot(forward.X(), forward.Y()));
    if (!valid || !joint_correction(yaw_axis, pitch_axis, error, correction) ||
      !joint_correction(yaw_axis, pitch_axis, actual_rate, damping))
    {
      // Singular/nonfinite feedback cannot send nonfinite forces into physics.
      joint_->SetForce(0, bounded_torque(-4.0 * joint_->GetVelocity(0), 5.0));
      pitch_joint_->SetForce(0, bounded_torque(-0.085 * pitch_joint_->GetVelocity(0), 1.0));
      return;
    }
    // A bounded local correction avoids large setpoint steps; damping measured
    // WORLD view rates allows the joints to cancel chassis spin without fighting it.
    joint_->SetForce(0, bounded_torque(
      80.0 * std::clamp(correction.yaw, -0.5, 0.5) - 4.0 * damping.yaw, 5.0));
    const double pitch_position = pitch_joint_->Position(0);
    const double target = std::clamp(pitch_position + correction.pitch,
      pitch_joint_->LowerLimit(0), pitch_joint_->UpperLimit(0));
    pitch_joint_->SetForce(0, bounded_torque(
      4.0 * std::clamp(target - pitch_position, -0.35, 0.35) -
      0.085 * damping.pitch + GravityCompensation(), 1.0));
  }

  void Update(const gazebo::common::UpdateInfo & info)
  {
    double yaw = 0.0, pitch = 0.0;
    bool fresh = false;
    {
      std::lock_guard<std::mutex> lock(look_mutex_);
      fresh = have_look_ &&
        std::chrono::duration<double>(std::chrono::steady_clock::now() - last_look_).count() < 0.5;
      yaw = look_yaw_;
      pitch = look_pitch_;
    }
    if (fresh) {
      ApplyLook(yaw, pitch);
      fps_active_ = true;
    } else {
      const bool requested = requested_.load();
      // Returning from FPS captures the ACTUAL position, never an old look target.
      if (requested != active_ || fps_active_) {
        if (requested) {
          world_heading_ = gimbal_->WorldPose().Rot().Yaw();
        } else {
          relative_target_ = joint_->Position(0);
        }
        active_ = requested;
      }
      if (fps_active_) {
        pitch_target_ = pitch_joint_->Position(0);
      }
      fps_active_ = false;
      if (active_) {
        const double current = joint_->Position(0);
        relative_target_ = hold_heading(
          current, gimbal_->WorldPose().Rot().Yaw() - current, world_heading_);
      }
      const double error = wrap_angle(relative_target_ - joint_->Position(0));
      const double rate = active_ ? gimbal_->WorldAngularVel().Z() : joint_->GetVelocity(0);
      joint_->SetForce(0, bounded_torque(80.0 * error - 4.0 * rate, 5.0));
      pitch_joint_->SetForce(0, bounded_torque(
        4.0 * (pitch_target_ - pitch_joint_->Position(0)) -
        0.085 * pitch_joint_->GetVelocity(0) + GravityCompensation(), 1.0));
    }
    if (info.simTime < last_publish_ ||
      (info.simTime - last_publish_).Double() >= 1.0 / 50.0)
    {
      last_publish_ = info.simTime;
      sensor_msgs::msg::JointState state;
      state.header.stamp.sec = static_cast<int32_t>(info.simTime.sec);
      state.header.stamp.nanosec = static_cast<uint32_t>(info.simTime.nsec);
      state.name = {"gimbal_yaw_joint", "gimbal_pitch_joint"};
      state.position = {joint_->Position(0), pitch_joint_->Position(0)};
      state.velocity = {joint_->GetVelocity(0), pitch_joint_->GetVelocity(0)};
      state.effort = {joint_->GetForce(0), pitch_joint_->GetForce(0)};
      states_->publish(state);
      auto message = PoseMessage(gimbal_->WorldPose());
      message.header = state.header;
      message.header.frame_id = "world";
      pose_->publish(message);
      message.pose = PoseMessage(CameraPose()).pose;
      view_->publish(message);
    }
  }

  static geometry_msgs::msg::PoseStamped PoseMessage(const ignition::math::Pose3d & actual)
  {
    geometry_msgs::msg::PoseStamped pose;
    pose.pose.position.x = actual.Pos().X();
    pose.pose.position.y = actual.Pos().Y();
    pose.pose.position.z = actual.Pos().Z();
    pose.pose.orientation.x = actual.Rot().X();
    pose.pose.orientation.y = actual.Rot().Y();
    pose.pose.orientation.z = actual.Rot().Z();
    pose.pose.orientation.w = actual.Rot().W();
    return pose;
  }

  gazebo::physics::ModelPtr model_;
  gazebo::physics::JointPtr joint_, pitch_joint_;
  gazebo::physics::LinkPtr gimbal_, pitch_link_;
  ignition::math::Vector3d camera_offset_;
  gazebo_ros::Node::SharedPtr node_;
  gazebo::event::ConnectionPtr update_;
  rclcpp::Subscription<std_msgs::msg::Bool>::SharedPtr command_;
  rclcpp::Subscription<geometry_msgs::msg::Vector3Stamped>::SharedPtr look_;
  rclcpp::Publisher<sensor_msgs::msg::JointState>::SharedPtr states_;
  rclcpp::Publisher<geometry_msgs::msg::PoseStamped>::SharedPtr pose_, view_;
  std::atomic<bool> requested_{false};
  std::mutex look_mutex_;
  std::chrono::steady_clock::time_point last_look_;
  bool have_look_{false};
  double look_yaw_{0.0}, look_pitch_{0.0};
  bool active_{false}, fps_active_{false};
  double world_heading_{0.0}, relative_target_{0.0}, pitch_target_{0.0};
  gazebo::common::Time last_publish_;
};

GZ_REGISTER_MODEL_PLUGIN(GimbalStabilizer)
}  // namespace sentry_sim
