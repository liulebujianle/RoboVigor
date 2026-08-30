import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/ethan/RoboVigor/sentinel_ws/install/sentinel_decision'
