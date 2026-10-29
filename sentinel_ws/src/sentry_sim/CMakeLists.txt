cmake_minimum_required(VERSION 3.8)
project(sentry_sim)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(gazebo REQUIRED)
find_package(gazebo_ros REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(tf2_ros REQUIRED)

add_library(sentry_gimbal_stabilizer SHARED src/gimbal_stabilizer.cpp)
target_compile_features(sentry_gimbal_stabilizer PUBLIC cxx_std_17)
target_include_directories(sentry_gimbal_stabilizer PRIVATE include ${GAZEBO_INCLUDE_DIRS})
target_link_libraries(sentry_gimbal_stabilizer ${GAZEBO_LIBRARIES})
ament_target_dependencies(sentry_gimbal_stabilizer
  gazebo_ros rclcpp std_msgs sensor_msgs geometry_msgs)
install(TARGETS sentry_gimbal_stabilizer LIBRARY DESTINATION lib)
ament_export_libraries(sentry_gimbal_stabilizer)
add_library(sentry_omni_drive SHARED src/omni_drive.cpp)
target_compile_features(sentry_omni_drive PUBLIC cxx_std_17)
target_include_directories(sentry_omni_drive PRIVATE include ${GAZEBO_INCLUDE_DIRS})
target_link_libraries(sentry_omni_drive ${GAZEBO_LIBRARIES})
ament_target_dependencies(sentry_omni_drive
  gazebo_ros rclcpp sensor_msgs geometry_msgs nav_msgs tf2_ros)
install(TARGETS sentry_omni_drive LIBRARY DESTINATION lib)
ament_export_libraries(sentry_omni_drive)
# uncomment the following section in order to fill in
# further dependencies manually.
# find_package(<dependency> REQUIRED)

if(BUILD_TESTING)
  find_package(Python3 REQUIRED COMPONENTS Interpreter)
  add_executable(test_gimbal_math test/test_gimbal_math.cpp)
  target_include_directories(test_gimbal_math PRIVATE include)
  add_test(NAME gimbal_heading_math COMMAND test_gimbal_math)
  add_executable(test_omni_kinematics test/test_omni_kinematics.cpp)
  target_include_directories(test_omni_kinematics PRIVATE include)
  add_test(NAME omni_contact_kinematics COMMAND test_omni_kinematics)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

# 将模型安装到包的 share 目录，后续启动文件通过包名查找模型。
install(DIRECTORY urdf launch config
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
