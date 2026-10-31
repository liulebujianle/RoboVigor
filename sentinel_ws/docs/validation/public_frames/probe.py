from pathlib import Path
import os,time,subprocess,signal,json,math
import rclpy
from rclpy.qos import QoSProfile,DurabilityPolicy,ReliabilityPolicy
from rclpy.time import Time
from tf2_msgs.msg import TFMessage
from tf2_ros import Buffer
from nav_msgs.msg import Odometry
from sensor_msgs.msg import JointState
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool
out=Path('/tmp/robovigor-frame-validation');out.mkdir(exist_ok=True);log=(out/'launch.log').open('w')
p=subprocess.Popen(['ros2','launch','sentry_bringup','sim_teleop.launch.py','gui:=false','rviz:=false','keyboard:=false','control_session:=verify_frames'],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
rclpy.init();n=rclpy.create_node('frame_integration_probe');pub=n.create_publisher(Twist,'/teleop/verify_frames/cmd_vel',1);mode=n.create_publisher(Bool,'/teleop/verify_frames/spin_mode',1)
public,full=Buffer(),Buffer();seen_public=set();seen_full=set();odom=[];joints={};messages=[0,0]
def transform(buffer,seen,static,index):
 def callback(msg):
  messages[index]+=1
  for t in msg.transforms:
   seen.add(t.child_frame_id)
   (buffer.set_transform_static if static else buffer.set_transform)(t,'probe')
 return callback
retained=QoSProfile(depth=100,reliability=ReliabilityPolicy.RELIABLE,durability=DurabilityPolicy.TRANSIENT_LOCAL)
subs=[]
def js(m):
 for i,name in enumerate(m.name):joints[name]=m.position[i]
subs.extend([n.create_subscription(Odometry,'/odom',odom.append,20),n.create_subscription(JointState,'/joint_states',js,20)])
def stamp():
 s=odom[-1].header.stamp;return s.sec+s.nanosec*1e-9
def pump(seconds,command=(0.,0.,0.),spin=False):
 start=stamp() if odom else None;end=time.monotonic()+seconds;deadline=time.monotonic()+max(20,seconds*5)
 while (stamp()-start<seconds) if start is not None else (time.monotonic()<end):
  m=Twist();m.linear.x,m.linear.y,m.angular.z=command;pub.publish(m);mode.publish(Bool(data=spin));rclpy.spin_once(n,timeout_sec=.005)
  assert p.poll() is None,'Launch stopped';assert time.monotonic()<deadline,'Simulation stalled'
def yaw(t):
 q=t.transform.rotation;return math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))
records={}
try:
 deadline=time.monotonic()+40
 while not odom and time.monotonic()<deadline:pump(.1)
 assert odom,'No physical model state'
 # Subscribe after spawn/static publication to test retained snapshots.
 pump(.6)
 for topic,buffer,seen,static,index in [('/tf',public,seen_public,False,0),('/tf_static',public,seen_public,True,0),('/sentry_description/tf_full',full,seen_full,False,1),('/sentry_description/tf_static_full',full,seen_full,True,1)]:
  subs.append(n.create_subscription(TFMessage,topic,transform(buffer,seen,static,index),retained if static else 100))
 pump(1.)
 expected={'odom','base_link','chassis_link','wheels_link','gimbal_yaw_link','lidar_link','lidar_aux_link','camera_link','camera_optical_frame','gun_link','muzzle_link'}
 assert expected<=seen_public,(expected-seen_public)
 assert not any(name.startswith(('wheel_','roller_')) for name in seen_public),seen_public
 assert 'wheel_1_link' in seen_full and 'roller_112_link' in seen_full
 assert public.can_transform('world','muzzle_link',Time())
 assert full.can_transform('world','roller_112_link',Time())
 assert not public.can_transform('world','wheel_1_link',Time())
 records['public_children']=sorted(seen_public);records['full_children_count']=len(seen_full)
 records['sensor_world_positions']={}
 for frame in ['lidar_link','lidar_aux_link','camera_link','camera_optical_frame','gun_link','muzzle_link']:
  t=public.lookup_transform('world',frame,Time()).transform.translation;records['sensor_world_positions'][frame]=[t.x,t.y,t.z]
 initial=joints['wheel_1_joint'];pump(.8,(.3,0.,0.));records['wheel_angle_change']=joints['wheel_1_joint']-initial
 assert abs(records['wheel_angle_change'])>.5
 pump(.7)
 initial={f:yaw(public.lookup_transform('world',f,Time())) for f in ['camera_link','gun_link','lidar_link']}
 pump(1.5,(0.,0.,3.),True)
 records['world_heading_drift']={f:math.atan2(math.sin(yaw(public.lookup_transform('world',f,Time()))-a),math.cos(yaw(public.lookup_transform('world',f,Time()))-a)) for f,a in initial.items()}
 assert max(abs(v) for v in records['world_heading_drift'].values())<.02,records
 pump(1.)
 records['message_counts']=messages
 assert messages[0]<2000 and messages[1]<2500,'TF feedback loop'
 assert not any(name.startswith(('wheel_','roller_')) for name in seen_public)
 (out/'metrics.json').write_text(json.dumps(records,indent=2)+'\n');print('PASS',json.dumps(records),flush=True)
finally:
 pub.publish(Twist());mode.publish(Bool(data=False))
 if p.poll() is None:
  os.kill(p.pid,signal.SIGINT)
  try:p.wait(timeout=15)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=5)
 log.close();n.destroy_node();rclpy.try_shutdown()
