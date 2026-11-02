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

# 两个插件共用构建设置，各自的额外依赖单独声明。
foreach(plugin IN ITEMS gimbal_stabilizer omni_drive)
  set(target sentry_${plugin})
  add_library(${target} SHARED src/${plugin}.cpp)
  target_compile_features(${target} PUBLIC cxx_std_17)
  target_include_directories(${target} PRIVATE include ${GAZEBO_INCLUDE_DIRS})
  target_link_libraries(${target} ${GAZEBO_LIBRARIES})
  ament_target_dependencies(${target} gazebo_ros rclcpp sensor_msgs geometry_msgs)
  install(TARGETS ${target} LIBRARY DESTINATION lib)
  ament_export_libraries(${target})
endforeach()
ament_target_dependencies(sentry_gimbal_stabilizer std_msgs)
ament_target_dependencies(sentry_omni_drive nav_msgs tf2_ros)

if(BUILD_TESTING)
  add_executable(test_gimbal_math test/test_gimbal_math.cpp)
  target_include_directories(test_gimbal_math PRIVATE include)
  add_test(NAME gimbal_heading_math COMMAND test_gimbal_math)
  add_executable(test_omni_kinematics test/test_omni_kinematics.cpp)
  target_include_directories(test_omni_kinematics PRIVATE include)
  add_test(NAME omni_contact_kinematics COMMAND test_omni_kinematics)
  find_package(ament_lint_auto REQUIRED)
  # 保留原有 lint 排除设置。
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

# 将模型安装到包的 share 目录，后续启动文件通过包名查找模型。
install(DIRECTORY urdf launch config
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
