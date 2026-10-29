import os
os.environ['QT_QPA_PLATFORM']='offscreen'
from pathlib import Path
import sys,time,math,json,signal,subprocess
import rclpy
from ament_index_python.packages import get_package_prefix
from nav_msgs.msg import Odometry
from geometry_msgs.msg import PoseStamped,Twist
from std_msgs.msg import Bool
from PyQt5.QtWidgets import QApplication
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt
sys.path.insert(0,str(Path(get_package_prefix('sentry_motion'))/'lib/sentry_motion'))
from keyboard_window import KeyboardWindow
out=Path('/tmp/robovigor-control-session-validation');out.mkdir(exist_ok=True)
log=(out/'launch.log').open('w')
p=subprocess.Popen(['ros2','launch','sentry_bringup','sim_teleop.launch.py','gui:=false','rviz:=false','keyboard:=false','control_session:=verify_keys'],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
rclpy.init();n=rclpy.create_node('held_key_integration');app=QApplication([])
window=KeyboardWindow(n,'/teleop/verify_keys');window.show();app.processEvents()
od=[];poses=[];cmds=[];modes=[]
subs=[n.create_subscription(Odometry,'/odom',lambda m:od.append((time.monotonic(),m)),50),n.create_subscription(PoseStamped,'/gimbal_pose',lambda m:poses.append((time.monotonic(),m)),50),n.create_subscription(Twist,'/cmd_vel',lambda m:cmds.append((time.monotonic(),m)),50),n.create_subscription(Bool,'/spin_mode',lambda m:modes.append(m.data),50)]
old=n.create_publisher(Twist,'/teleop/cmd_vel',1);oldmode=n.create_publisher(Bool,'/teleop/spin_mode',1)
def pump(duration,contaminate=False):
 def simtime():
  stamp=od[-1][1].header.stamp
  return stamp.sec+stamp.nanosec*1e-9
 start_sim=simtime() if od else None
 end=time.monotonic()+duration
 deadline=time.monotonic()+max(10,duration*5)
 while (simtime()-start_sim<duration) if start_sim is not None else (time.monotonic()<end):
  app.processEvents();rclpy.spin_once(n,timeout_sec=.001)
  if contaminate:
   m=Twist();m.linear.x=.8;m.angular.z=3.;old.publish(m);oldmode.publish(Bool(data=True))
  time.sleep(.002)
  assert p.poll() is None,'Launch stopped'
  assert time.monotonic()<deadline,'Simulation stalled'
def yaw(q):return math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))
def err(a,b):return math.atan2(math.sin(a-b),math.cos(a-b))
def pos():
 v=od[-1][1].pose.pose.position;return v.x,v.y
metrics={}
try:
 end=time.monotonic()+40
 while not od and time.monotonic()<end:pump(.1)
 assert od and poses,'Model did not publish actual state'
 pump(2)
 origin=pos();assert math.dist(origin,(1.25,6.75))<.03,origin
 pump(1,True)
 metrics['startup_drift_m']=math.dist(pos(),origin)
 assert metrics['startup_drift_m']<.015 and not modes[-1]
 publishers=n.get_publishers_info_by_topic('/cmd_vel');assert len(publishers)==1,len(publishers)
 start=time.monotonic();QTest.keyPress(window,Qt.Key_W);pump(1.1)
 forward=pos();metrics['held_forward_m']=math.dist(forward,origin)
 held=[m.linear.x for t,m in cmds if t>start+.2]
 assert held and min(held)>.79,'Command stopped during one held press'
 assert metrics['held_forward_m']>.65
 QTest.keyRelease(window,Qt.Key_W);pump(.8)
 actual=od[-1][1].twist.twist;assert math.hypot(actual.linear.x,actual.linear.y)<.03
 QTest.keyPress(window,Qt.Key_S);pump(1.1);QTest.keyRelease(window,Qt.Key_S);pump(.8)
 heading=yaw(poses[-1][1].pose.orientation);start=time.monotonic();QTest.keyClick(window,Qt.Key_X);pump(2.6)
 body=[yaw(m.pose.pose.orientation) for t,m in od if t>start]
 metrics['chassis_rotation_rad']=sum(err(b,a) for a,b in zip(body,body[1:]))
 metrics['gimbal_max_error_rad']=max(abs(err(yaw(m.pose.orientation),heading)) for t,m in poses if t>start+.15)
 assert metrics['chassis_rotation_rad']>6
 assert metrics['gimbal_max_error_rad']<.01
 line_origin=pos();line_start=time.monotonic();QTest.keyPress(window,Qt.Key_W);pump(1.6);QTest.keyRelease(window,Qt.Key_W);pump(.6)
 path=[(m.pose.pose.position.x-line_origin[0],m.pose.pose.position.y-line_origin[1]) for t,m in od if t>line_start]
 metrics['straight_cross_track_max_m']=max(abs(-math.sin(heading)*x+math.cos(heading)*y) for x,y in path)
 dx,dy=path[-1];metrics['straight_distance_m']=math.cos(heading)*dx+math.sin(heading)*dy
 (out/'trajectory.json').write_text(json.dumps(dict(origin=line_origin,heading=heading,path=path,metrics=metrics),indent=2))
 assert metrics['straight_cross_track_max_m']<.05,metrics
 assert metrics['straight_distance_m']>1.,metrics
 assert od[-1][1].twist.twist.angular.z>2.5
 QTest.keyClick(window,Qt.Key_C);pump(1.2)
 actual=od[-1][1].twist.twist;metrics['stopped_wz']=actual.angular.z
 assert not modes[-1] and abs(actual.angular.z)<.06 and math.hypot(actual.linear.x,actual.linear.y)<.03
 (out/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n');print('PASS',json.dumps(metrics),flush=True)
finally:
 (out/'latest_metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
 window.close();app.processEvents()
 if p.poll() is None:
  os.kill(p.pid,signal.SIGINT)
  try:p.wait(timeout=15)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=5)
 n.destroy_node();rclpy.try_shutdown();log.close()
