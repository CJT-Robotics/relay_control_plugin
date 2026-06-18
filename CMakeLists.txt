cmake_minimum_required(VERSION 3.0.2)
project(relay_control_plugin)

find_package(catkin REQUIRED COMPONENTS
  rospy
  rqt_gui
  rqt_gui_py
  std_msgs
)

catkin_package(
)