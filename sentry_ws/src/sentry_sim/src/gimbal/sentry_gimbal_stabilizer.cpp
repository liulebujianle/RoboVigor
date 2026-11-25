// Copyright 2026 RoboVigor contributors
// SPDX-License-Identifier: Apache-2.0
#include <atomic>
#include <cmath>
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
// 两台导航雷达共用转台 yaw 关节。
class GimbalStabilizer : public gazebo::ModelPlugin
{
public:
  void Load(gazebo::physics::ModelPtr model, sdf::ElementPtr sdf) override
  {
    node_ = gazebo_ros::Node::Get(sdf);
    joint_ = model->GetJoint("gimbal_yaw_joint");
    if (!joint_) {
      RCLCPP_ERROR(node_->get_logger(), "Missing gimbal_yaw_joint in the navigation model");
      return;
    }
    small_yaw_ = model->GetJoint("small_yaw_joint");
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
    RCLCPP_INFO(node_->get_logger(), "Navigation turntable ready on /spin_mode");
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
      relative_target_ = hold_heading(
        current, gimbal_->WorldPose().Rot().Yaw() - current, world_heading_);
    }
    const double error = wrap_angle(relative_target_ - joint_->Position(0));
    const double rate = active_ ? gimbal_->WorldAngularVel().Z() : joint_->GetVelocity(0);
    joint_->SetForce(0, bounded_torque(80.0 * error - 4.0 * rate, 5.0));
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
      state.effort = {joint_->GetForce(0)};
      // 空载小轴自由转动，只读取 Gazebo 的实际关节状态。
      if (small_yaw_) {
        state.name.push_back(small_yaw_->GetName());
        state.position.push_back(small_yaw_->Position(0));
        state.velocity.push_back(small_yaw_->GetVelocity(0));
        state.effort.push_back(small_yaw_->GetForce(0));
      }
      states_->publish(state);
      auto message = PoseMessage(gimbal_->WorldPose());
      message.header = state.header;
      message.header.frame_id = "world";
      pose_->publish(message);
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

  gazebo::physics::JointPtr joint_;
  gazebo::physics::JointPtr small_yaw_;
  gazebo::physics::LinkPtr gimbal_;
  gazebo_ros::Node::SharedPtr node_;
  gazebo::event::ConnectionPtr update_;
  rclcpp::Subscription<std_msgs::msg::Bool>::SharedPtr command_;
  rclcpp::Publisher<sensor_msgs::msg::JointState>::SharedPtr states_;
  rclcpp::Publisher<geometry_msgs::msg::PoseStamped>::SharedPtr pose_;
  std::atomic<bool> requested_{false};
  bool active_{false};
  double world_heading_{0.0}, relative_target_{0.0};
  gazebo::common::Time last_publish_;
};

GZ_REGISTER_MODEL_PLUGIN(GimbalStabilizer)
}  // namespace sentry_sim
