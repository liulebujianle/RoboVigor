from pathlib import Path
import os,time,subprocess,signal,json,math
import xml.etree.ElementTree as ET
from collections import Counter
import rclpy
from rclpy.qos import QoSProfile,DurabilityPolicy
from rclpy.time import Time
from tf2_msgs.msg import TFMessage
from tf2_ros import Buffer
from nav_msgs.msg import Odometry
from sensor_msgs.msg import JointState
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool,String
out=Path('/tmp/robovigor-per-wheel-validation');out.mkdir(exist_ok=True);log=(out/'launch.log').open('w')
p=subprocess.Popen(['ros2','launch','sentry_bringup','sim_teleop.launch.py','gui:=false','rviz:=false','keyboard:=false','control_session:=verify_axles'],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
rclpy.init();node=rclpy.create_node('per_wheel_tf_probe');buffer=Buffer();frames=set();od=[];display=[];physics=[];joints={};states={};wheel_transforms={}
retained=QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL)
static=QoSProfile(depth=100,durability=DurabilityPolicy.TRANSIENT_LOCAL)
def transforms(message,fixed=False):
 for t in message.transforms:
  frames.add(t.child_frame_id)
  if t.child_frame_id.startswith('wheel_'):
   key=(t.header.stamp.sec,t.header.stamp.nanosec)
   wheel_transforms.setdefault(key,{})[t.child_frame_id]=t
  (buffer.set_transform_static if fixed else buffer.set_transform)(t,'probe')
def joint(m):
 for i,name in enumerate(m.name):joints[name]=m.position[i]
 if 'wheel_1_joint' in m.name:states[(m.header.stamp.sec,m.header.stamp.nanosec)]={name:m.position[i] for i,name in enumerate(m.name)}
subs=[node.create_subscription(Odometry,'/odom',od.append,20),node.create_subscription(JointState,'/joint_states',joint,20),node.create_subscription(TFMessage,'/tf',transforms,100),node.create_subscription(TFMessage,'/tf_static',lambda m:transforms(m,True),static),node.create_subscription(String,'/robot_description',lambda m:display.append(m.data),retained),node.create_subscription(String,'/sentry_description/robot_description_physics',lambda m:physics.append(m.data),retained)]
pub=node.create_publisher(Twist,'/teleop/verify_axles/cmd_vel',1);mode=node.create_publisher(Bool,'/teleop/verify_axles/spin_mode',1)
def stamp():
 s=od[-1].header.stamp;return s.sec+s.nanosec*1e-9
def pump(duration,v=(0.,0.,0.),spin=False):
 initial=stamp() if od else None;end=time.monotonic()+duration;deadline=time.monotonic()+max(20,duration*5)
 while (stamp()-initial<duration) if initial is not None else (time.monotonic()<end):
  m=Twist();m.linear.x,m.linear.y,m.angular.z=v;pub.publish(m);mode.publish(Bool(data=spin));rclpy.spin_once(node,timeout_sec=.005)
  assert p.poll() is None,'Launch stopped';assert time.monotonic()<deadline,'Simulation stalled'
def quat(t):
 q=t.transform.rotation;return [q.x,q.y,q.z,q.w]
def difference(a,b):return 2*math.acos(min(1.,abs(sum(x*y for x,y in zip(a,b)))))
records={}
try:
 deadline=time.monotonic()+40
 while (not od or not display or not physics) and time.monotonic()<deadline:pump(.1)
 assert od and display and physics,'Missing description or physical state'
 pump(1.)
 wheels={f'wheel_{i}_link' for i in range(1,5)}
 assert {f for f in frames if f.startswith('wheel_')}==wheels,frames
 assert 'wheels_link' not in frames and not any(f.startswith('roller_') for f in frames)
 raw=ET.fromstring(physics[-1]);compact=ET.fromstring(display[-1])
 assert len(raw.findall("joint[@type='continuous']"))==117
 assert len(compact.findall("joint[@type='continuous']"))==5
 assert len(compact.findall('.//visual/geometry/mesh'))==118
 assert Counter(m.get('filename') for m in raw.findall('.//visual/geometry/mesh'))==Counter(m.get('filename') for m in compact.findall('.//visual/geometry/mesh'))
 assert compact.find("link[@name='wheels_link']") is None
 before={name:quat(buffer.lookup_transform('chassis_link',name,Time())) for name in wheels}
 positions={name:buffer.lookup_transform('chassis_link',name,Time()).transform.translation for name in wheels}
 old_x=od[-1].pose.pose.position.x;pump(.9,(.4,0.,0.))
 records['wheel_tf_rotation_rad']={name:difference(before[name],quat(buffer.lookup_transform('chassis_link',name,Time()))) for name in wheels}
 assert min(records['wheel_tf_rotation_rad'].values())>.7,records
 records['physical_forward_m']=od[-1].pose.pose.position.x-old_x;assert records['physical_forward_m']>.2
 records['wheel_positions']={}
 common=max(set(states)&{key for key,values in wheel_transforms.items() if len(values)==4})
 for i in range(1,5):
  name=f'wheel_{i}_link';tf=buffer.lookup_transform('chassis_link',name,Time());v=tf.transform.translation
  expected=list(map(float,raw.find(f"joint[@name='wheel_{i}_joint']/origin").get('xyz').split()))
  assert max(abs(a-b) for a,b in zip([v.x,v.y,v.z],expected))<1e-9
  tf=wheel_transforms[common][name];q=states[common][f'wheel_{i}_joint']
  axis=list(map(float,raw.find(f"joint[@name='wheel_{i}_joint']/axis").get('xyz').split()))
  expected_q=[a*math.sin(q/2) for a in axis]+[math.cos(q/2)]
  assert difference(quat(tf),expected_q)<1e-5,(name,q,quat(tf),expected_q)
  records['wheel_positions'][name]=[v.x,v.y,v.z]
 pump(.8)
 for frame in ['lidar_link','lidar_aux_link','camera_link','camera_optical_frame','gun_link','muzzle_link']:
  assert buffer.can_transform('world',frame,Time()),frame
 assert not node.get_publishers_info_by_topic('/sentry_description/wheel_visuals')
 assert not node.get_publishers_info_by_topic('/sentry_description/tf_full')
 records['public_frames']=sorted(frames);records['display_meshes']=118;records['physics_joints']=117;records['public_moving_joints']=5
 (out/'metrics.json').write_text(json.dumps(records,indent=2)+'\n');print('PASS',json.dumps(records),flush=True)
finally:
 pub.publish(Twist());mode.publish(Bool(data=False))
 if p.poll() is None:
  os.kill(p.pid,signal.SIGINT)
  try:p.wait(timeout=15)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=5)
 log.close();node.destroy_node();rclpy.try_shutdown()
