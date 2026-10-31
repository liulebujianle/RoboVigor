// Copyright 2026 RoboVigor contributors
// SPDX-License-Identifier: Apache-2.0
#include <atomic>
#include <algorithm>
#include <cstdint>
#include <functional>
#include <memory>

#include <gazebo/common/Events.hh>
#include <gazebo/common/Plugin.hh>
#include <gazebo/physics/physics.hh>
#include <gazebo_ros/node.hpp>
#include <geometry_msgs/msg/pose_stamped.hpp>
#include <sensor_msgs/msg/joint_state.hpp>
#include <std_msgs/msg/bool.hpp>

#include "sentry_sim/gimbal_math.hpp"

namespace sentry_sim
{
// Bounded yaw motor feedback; no link/joint pose or velocity assignment.
class GimbalStabilizer : public gazebo::ModelPlugin
{
public:
  void Load(gazebo::physics::ModelPtr model, sdf::ElementPtr sdf) override
  {
    model_ = model;
    node_ = gazebo_ros::Node::Get(sdf);
    joint_ = model_->GetJoint("gimbal_yaw_joint");
    if (!joint_) {
      RCLCPP_ERROR(node_->get_logger(), "Missing gimbal_yaw_joint in the robot model");
      return;
    }
    gimbal_ = joint_->GetChild();
    relative_target_ = joint_->Position(0);
    command_ = node_->create_subscription<std_msgs::msg::Bool>(
      "/spin_mode", 1, [this](const std_msgs::msg::Bool::SharedPtr message) {
        requested_.store(message->data);
      });
    states_ = node_->create_publisher<sensor_msgs::msg::JointState>("/joint_states", 10);
    pose_ = node_->create_publisher<geometry_msgs::msg::PoseStamped>("/gimbal_pose", 10);
    update_ = gazebo::event::Events::ConnectWorldUpdateBegin(
      std::bind(&GimbalStabilizer::Update, this, std::placeholders::_1));
    RCLCPP_INFO(node_->get_logger(), "Gimbal heading stabilizer ready on /spin_mode");
  }

  void Reset() override
  {
    requested_.store(false);
    active_ = false;
    last_publish_ = gazebo::common::Time::Zero;
    if (joint_) {
      relative_target_ = joint_->Position(0);
    }
  }

private:
  void Update(const gazebo::common::UpdateInfo & info)
  {
    const bool requested = requested_.load();
    if (requested != active_) {
      if (requested) {
        world_heading_ = gimbal_->WorldPose().Rot().Yaw();
      } else {
        relative_target_ = joint_->Position(0);
      }
      active_ = requested;
    }
    if (active_) {
      const double current = joint_->Position(0);
      // Use measured link orientation, including any small chassis tilt.
      relative_target_ = hold_heading(
        current, gimbal_->WorldPose().Rot().Yaw() - current, world_heading_);
    }
    const double error = relative_target_ - joint_->Position(0);
    const double wrapped_error = std::atan2(std::sin(error), std::cos(error));
    const double rate = active_ ? gimbal_->WorldAngularVel().Z() : joint_->GetVelocity(0);
    joint_->SetForce(0, std::clamp(80.0 * wrapped_error - 4.0 * rate, -5.0, 5.0));
    if (info.simTime < last_publish_ ||
      (info.simTime - last_publish_).Double() >= 1.0 / 50.0)
    {
      last_publish_ = info.simTime;
      sensor_msgs::msg::JointState state;
      state.header.stamp.sec = static_cast<int32_t>(info.simTime.sec);
      state.header.stamp.nanosec = static_cast<uint32_t>(info.simTime.nsec);
      state.name = {"gimbal_yaw_joint"};
      state.position = {joint_->Position(0)};
      state.velocity = {joint_->GetVelocity(0)};
      states_->publish(state);
      const auto actual = gimbal_->WorldPose();
      geometry_msgs::msg::PoseStamped pose;
      pose.header = state.header;
      pose.header.frame_id = "world";
      pose.pose.position.x = actual.Pos().X();
      pose.pose.position.y = actual.Pos().Y();
      pose.pose.position.z = actual.Pos().Z();
      pose.pose.orientation.x = actual.Rot().X();
      pose.pose.orientation.y = actual.Rot().Y();
      pose.pose.orientation.z = actual.Rot().Z();
      pose.pose.orientation.w = actual.Rot().W();
      pose_->publish(pose);
    }
  }

  gazebo::physics::ModelPtr model_;
  gazebo::physics::JointPtr joint_;
  gazebo::physics::LinkPtr gimbal_;
  gazebo_ros::Node::SharedPtr node_;
  gazebo::event::ConnectionPtr update_;
  rclcpp::Subscription<std_msgs::msg::Bool>::SharedPtr command_;
  rclcpp::Publisher<sensor_msgs::msg::JointState>::SharedPtr states_;
  rclcpp::Publisher<geometry_msgs::msg::PoseStamped>::SharedPtr pose_;
  std::atomic<bool> requested_{false};
  bool active_{false};
  double world_heading_{0.0};
  double relative_target_{0.0};
  gazebo::common::Time last_publish_;
};

GZ_REGISTER_MODEL_PLUGIN(GimbalStabilizer)
}  // namespace sentry_sim
