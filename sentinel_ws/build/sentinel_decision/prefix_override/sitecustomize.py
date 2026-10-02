import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/ethan/桌面/RoboVigor/sentinel_ws/install/sentinel_decision'
