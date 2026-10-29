from pathlib import Path
import json
import math
import os
import pty
import signal
import subprocess
import time

import rclpy
from geometry_msgs.msg import PoseStamped, Twist
from nav_msgs.msg import Odometry
from std_msgs.msg import Bool
from ament_index_python.packages import get_package_prefix

out = Path('/tmp/robovigor-wheel-validation/keyboard')
out.mkdir(parents=True, exist_ok=True)
rclpy.init()
probe = rclpy.create_node('sentry_spin_probe')
odoms, gimbals, commands, modes = [], [], [], []
subscriptions = [
    probe.create_subscription(Odometry, '/odom', lambda m: odoms.append((time.monotonic(), m)), 20),
    probe.create_subscription(PoseStamped, '/gimbal_pose', lambda m: gimbals.append((time.monotonic(), m)), 20),
    probe.create_subscription(Twist, '/cmd_vel', lambda m: commands.append((time.monotonic(), m)), 20),
    probe.create_subscription(Bool, '/spin_mode', lambda m: modes.append((time.monotonic(), m.data)), 20),
]

def yaw(q):
    return math.atan2(2*(q.w*q.z+q.x*q.y), 1-2*(q.y*q.y+q.z*q.z))

def angle_error(a, b):
    return math.atan2(math.sin(a-b), math.cos(a-b))

def pump(duration, key=None):
    end = time.monotonic() + duration
    next_key = 0
    while time.monotonic() < end:
        if key and time.monotonic() >= next_key:
            os.write(master, key.encode())
            next_key = time.monotonic() + 0.08
        rclpy.spin_once(probe, timeout_sec=0.01)

log = (out/'launch.log').open('w')
launch = subprocess.Popen(['ros2','launch','sentry_simulation','sim_teleop.launch.py',
                           'gui:=false','rviz:=false','keyboard:=false'],
                          stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
keyboard = None
master, slave = pty.openpty()
metrics = {}
try:
    deadline=time.monotonic()+35
    while time.monotonic()<deadline and (not odoms or not gimbals):
        rclpy.spin_once(probe,timeout_sec=0.1)
        assert launch.poll() is None, 'Unified teleop launch exited early'
    assert odoms and gimbals, 'Missing odometry or actual gimbal pose; see launch.log'
    executable=Path(get_package_prefix('sentry_simulation'))/'lib/sentry_simulation/keyboard_control.py'
    keyboard=subprocess.Popen([str(executable),'--keyboard'],stdin=slave,stdout=slave,stderr=slave,
                              start_new_session=True)
    os.close(slave)
    pump(.5)
    initial=odoms[-1][1].pose.pose.position.x
    pump(.5,'w'); os.write(master,b' ');pump(.25)
    forward=odoms[-1][1].pose.pose.position.x
    metrics['forward_displacement_m']=forward-initial
    assert forward-initial>.18, ('Forward too slow',forward-initial)
    pump(.5,'s');os.write(master,b' ');pump(.25)
    backward=odoms[-1][1].pose.pose.position.x
    metrics['backward_displacement_m']=backward-forward
    assert backward-forward<-.18, ('Backward failed',backward-forward)
    print('PASS: actual keyboard W/S drives the CAD sentry at increased speed',flush=True)
    baseline=yaw(gimbals[-1][1].pose.orientation)
    start=time.monotonic();os.write(master,b'x');pump(2.8)
    body=[yaw(m.pose.pose.orientation) for t,m in odoms if t>=start]
    rotation=sum(angle_error(b,a) for a,b in zip(body,body[1:]))
    cloud=[yaw(m.pose.orientation) for t,m in gimbals if t>=start+.2]
    drift=max(abs(angle_error(a,baseline)) for a in cloud)
    metrics['chassis_spin_rad']=rotation;metrics['max_gimbal_yaw_drift_rad']=drift
    assert rotation>6.0, ('Chassis did not make a full turn',rotation)
    assert drift<.05, ('Gimbal world heading moved',drift)
    print(f'PASS: chassis spin {rotation:.3f} rad; max actual gimbal drift {drift:.5f} rad',flush=True)
    pump(.3,'x')
    assert abs(commands[-1][1].angular.z-3.0)<.1, 'Repeated X disabled spin'
    position=odoms[-1][1].pose.pose.position
    sx,sy=position.x,position.y
    pump(.5,'w');pump(.4)
    position=odoms[-1][1].pose.pose.position
    metrics['spin_forward_dx_m']=position.x-sx;metrics['spin_forward_dy_m']=position.y-sy
    assert position.x-sx>.15 and abs(position.y-sy)<.12, ('Spin movement is not gimbal-relative',metrics)
    os.write(master,b'c');pump(.4)
    assert abs(commands[-1][1].angular.z)<.01 and not modes[-1][1], 'C did not stop spin'
    os.write(master,b'x');pump(.3);os.write(master,b' ');pump(.4)
    assert abs(commands[-1][1].angular.z)<.01 and not modes[-1][1], 'Space did not stop spin'
    os.write(master,b'x');pump(.4)
    assert modes[-1][1], 'Spin did not re-enable'
    os.killpg(keyboard.pid,signal.SIGKILL);keyboard.wait(timeout=5);pump(.75)
    cmd=commands[-1][1]
    assert max(abs(cmd.linear.x),abs(cmd.linear.y),abs(cmd.angular.z))<.01
    assert not modes[-1][1], 'Watchdog left spin enabled after keyboard loss'
    actual=odoms[-1][1].twist.twist
    metrics['stopped_yaw_rate_rad_s']=actual.angular.z
    metrics['stopped_linear_speed_m_s']=math.hypot(actual.linear.x,actual.linear.y)
    assert abs(actual.angular.z)<.1 and math.hypot(actual.linear.x,actual.linear.y)<.1, 'Actual chassis did not stop'
    print('PASS: repeated X, gimbal-relative translation, C, space and lost-keyboard stop',flush=True)
    for name in ['rmul_2027','robovigor_sentry']:
        result=subprocess.run(['gz','model','-m',name,'-i'],capture_output=True,text=True,timeout=8)
        assert result.returncode==0 and name in result.stdout,(name,result.stderr)
        (out/(name+'.txt')).write_text(result.stdout)
    (out/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
    print('PASS: map and actual articulated sentry both exist in Gazebo',flush=True)
finally:
    if keyboard is not None and keyboard.poll() is None:
        os.killpg(keyboard.pid,signal.SIGINT)
        try:keyboard.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(keyboard.pid,signal.SIGTERM);keyboard.wait(timeout=5)
    os.close(master)
    if launch.poll() is None:
        os.kill(launch.pid,signal.SIGINT)
        try:launch.wait(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(launch.pid,signal.SIGTERM);launch.wait(timeout=5)
    log.close()
    probe.destroy_node();rclpy.shutdown()
