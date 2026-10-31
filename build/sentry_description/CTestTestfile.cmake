# CMake generated Testfile for 
# Source directory: /home/ethan/RoboVigor/sentinel_ws/src/sentry_description
# Build directory: /home/ethan/RoboVigor/build/sentry_description
# 
# This file includes the relevant testing commands required for 
# testing this directory and lists subdirectories to be tested as well.
add_test(cad_model_resources "/usr/bin/python3" "-m" "pytest" "-q" "/home/ethan/RoboVigor/sentinel_ws/src/sentry_description/test")
set_tests_properties(cad_model_resources PROPERTIES  _BACKTRACE_TRIPLES "/home/ethan/RoboVigor/sentinel_ws/src/sentry_description/CMakeLists.txt;6;add_test;/home/ethan/RoboVigor/sentinel_ws/src/sentry_description/CMakeLists.txt;0;")
