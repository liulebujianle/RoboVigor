// Copyright 2026 RoboVigor contributors
// SPDX-License-Identifier: Apache-2.0
#include <algorithm>
#include <chrono>
#include <cmath>
#include <functional>
#include <memory>
#include <mutex>
#include <vector>

#include <gazebo/common/Events.hh>
#include <gazebo/common/Plugin.hh>
#include <gazebo/physics/physics.hh>
#include <gazebo_ros/node.hpp>
#include <geometry_msgs/msg/transform_stamped.hpp>
#include <geometry_msgs/msg/twist.hpp>
#include <nav_msgs/msg/odometry.hpp>
#include <sensor_msgs/msg/joint_state.hpp>
#include <tf2_ros/transform_broadcaster.h>

#include "sentry_sim/omni_kinematics.hpp"

namespace sentry_sim
{
class OmniDrive : public gazebo::ModelPlugin
{
public:
  void Load(gazebo::physics::ModelPtr model, sdf::ElementPtr sdf) override
  {
    model_ = model;
    node_ = gazebo_ros::Node::Get(sdf);
    if (!sdf->HasElement("wheel")) {
      RCLCPP_ERROR(node_->get_logger(), "Wheel geometry is missing");
      return;
    }
    for (auto element = sdf->GetElement("wheel"); element;
      element = element->GetNextElement("wheel"))
    {
      Wheel wheel;
      wheel.joint = model_->GetJoint(element->Get<std::string>("joint"));
      wheel.radius = element->Get<double>("radius");
      if (!wheel.joint || wheel.radius <= 0.0) {
        RCLCPP_ERROR(node_->get_logger(), "Invalid driven wheel joint or radius");
        return;
      }
      const auto pose = model_->WorldPose();
      wheel.axis = pose.Rot().RotateVectorReverse(wheel.joint->GlobalAxis(0));
      wheel.center = pose.Rot().RotateVectorReverse(wheel.joint->Anchor(0) - pose.Pos());
      wheels_.push_back(wheel);
    }
    for (auto joint : model_->GetJoints()) {
      if (joint->GetName().find("wheel_") == 0 || joint->GetName().find("roller_") == 0) {
        joints_.push_back(joint);
      }
    }
    command_ = node_->create_subscription<geometry_msgs::msg::Twist>(
      "/cmd_vel", 1, [this](const geometry_msgs::msg::Twist::SharedPtr input) {
        std::lock_guard<std::mutex> lock(mutex_);
        if (std::isfinite(input->linear.x) && std::isfinite(input->linear.y) &&
        std::isfinite(input->angular.z))
        {
          desired_ = *input;
          const double scale = std::min(
            1.0, 1.2 / std::max(std::hypot(desired_.linear.x, desired_.linear.y), 1e-9));
          desired_.linear.x *= scale;
          desired_.linear.y *= scale;
          desired_.angular.z = std::clamp(desired_.angular.z, -4.0, 4.0);
        } else {
          desired_ = geometry_msgs::msg::Twist();
        }
        last_command_ = std::chrono::steady_clock::now();
      });
    odometry_ = node_->create_publisher<nav_msgs::msg::Odometry>("/odom", 10);
    states_ = node_->create_publisher<sensor_msgs::msg::JointState>("/joint_states", 10);
    transforms_ = std::make_unique<tf2_ros::TransformBroadcaster>(node_);
    update_ = gazebo::event::Events::ConnectWorldUpdateBegin(
      std::bind(&OmniDrive::Update, this, std::placeholders::_1));
    RCLCPP_INFO(
      node_->get_logger(), "Torque drive ready: %zu axles, %zu measured wheel joints",
      wheels_.size(), joints_.size());
  }

  void Reset() override
  {
    std::lock_guard<std::mutex> lock(mutex_);
    desired_ = geometry_msgs::msg::Twist();
    for (auto & wheel : wheels_) {
      wheel.integral = 0.0;
    }
    last_update_ = last_publish_ = gazebo::common::Time::Zero;
  }

private:
  struct Wheel
  {
    gazebo::physics::JointPtr joint;
    ignition::math::Vector3d axis, center;
    double radius{0.0};
    double integral{0.0};
  };

  void Update(const gazebo::common::UpdateInfo & info)
  {
    const double dt = std::clamp((info.simTime - last_update_).Double(), 0.0, 0.01);
    last_update_ = info.simTime;
    geometry_msgs::msg::Twist desired;
    {
      std::lock_guard<std::mutex> lock(mutex_);
      if (std::chrono::duration<double>(
          std::chrono::steady_clock::now() - last_command_).count() < 0.5)
      {
        desired = desired_;
      }
    }
    const bool braking = std::abs(desired.linear.x) + std::abs(desired.linear.y) +
      std::abs(desired.angular.z) < 1e-9;
    for (auto & wheel : wheels_) {
      const double target = wheel_rate(
        wheel.axis.X(), wheel.axis.Y(), wheel.center.X(), wheel.center.Y(), wheel.radius,
        desired.linear.x, desired.linear.y, desired.angular.z);
      const double error = target - wheel.joint->GetVelocity(0);
      if (braking) {
        wheel.integral = 0.0;
      }
      const double torque = 0.35 * error + 0.15 * wheel.integral;
      if (!braking && (std::abs(torque) < 1.2 || error * torque < 0.0)) {
        wheel.integral = std::clamp(wheel.integral + error * dt, -5.0, 5.0);
      }
      wheel.joint->SetForce(0, std::clamp(torque, -1.2, 1.2));
    }
    if (info.simTime >= last_publish_ &&
      (info.simTime - last_publish_).Double() < 0.02)
    {
      return;
    }
    last_publish_ = info.simTime;
    nav_msgs::msg::Odometry odom;
    odom.header.stamp.sec = static_cast<int32_t>(info.simTime.sec);
    odom.header.stamp.nanosec = static_cast<uint32_t>(info.simTime.nsec);
    odom.header.frame_id = "odom";
    odom.child_frame_id = "base_link";
    const auto pose = model_->WorldPose();
    odom.pose.pose.position.x = pose.Pos().X();
    odom.pose.pose.position.y = pose.Pos().Y();
    odom.pose.pose.position.z = pose.Pos().Z();
    odom.pose.pose.orientation.x = pose.Rot().X();
    odom.pose.pose.orientation.y = pose.Rot().Y();
    odom.pose.pose.orientation.z = pose.Rot().Z();
    odom.pose.pose.orientation.w = pose.Rot().W();
    const auto linear = pose.Rot().RotateVectorReverse(model_->WorldLinearVel());
    const auto angular = pose.Rot().RotateVectorReverse(model_->WorldAngularVel());
    odom.twist.twist.linear.x = linear.X();
    odom.twist.twist.linear.y = linear.Y();
    odom.twist.twist.linear.z = linear.Z();
    odom.twist.twist.angular.x = angular.X();
    odom.twist.twist.angular.y = angular.Y();
    odom.twist.twist.angular.z = angular.Z();
    odometry_->publish(odom);
    geometry_msgs::msg::TransformStamped transform;
    transform.header = odom.header;
    transform.child_frame_id = odom.child_frame_id;
    transform.transform.translation.x = pose.Pos().X();
    transform.transform.translation.y = pose.Pos().Y();
    transform.transform.translation.z = pose.Pos().Z();
    transform.transform.rotation = odom.pose.pose.orientation;
    transforms_->sendTransform(transform);
    sensor_msgs::msg::JointState state;
    state.header = odom.header;
    for (const auto & joint : joints_) {
      state.name.push_back(joint->GetName());
      state.position.push_back(joint->Position(0));
      state.velocity.push_back(joint->GetVelocity(0));
      state.effort.push_back(joint->GetForce(0));
    }
    states_->publish(state);
  }

  gazebo::physics::ModelPtr model_;
  gazebo_ros::Node::SharedPtr node_;
  std::vector<Wheel> wheels_;
  std::vector<gazebo::physics::JointPtr> joints_;
  std::mutex mutex_;
  geometry_msgs::msg::Twist desired_;
  std::chrono::steady_clock::time_point last_command_;
  gazebo::common::Time last_update_, last_publish_;
  gazebo::event::ConnectionPtr update_;
  rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr command_;
  rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr odometry_;
  rclcpp::Publisher<sensor_msgs::msg::JointState>::SharedPtr states_;
  std::unique_ptr<tf2_ros::TransformBroadcaster> transforms_;
};
GZ_REGISTER_MODEL_PLUGIN(OmniDrive)
}  // namespace sentry_sim
