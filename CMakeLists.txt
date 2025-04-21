cmake_minimum_required(VERSION 3.5)
project(web_dyn_reconf)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclpy REQUIRED)
find_package(rcl_interfaces REQUIRED)


install(
  DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)

install(PROGRAMS
  scripts/dyn_reconf_remi.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()