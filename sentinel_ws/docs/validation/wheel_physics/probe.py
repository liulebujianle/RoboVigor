from pathlib import Path
import argparse,json,math,os,signal,subprocess,time
import rclpy
from geometry_msgs.msg import Twist,PoseStamped
from nav_msgs.msg import Odometry
from sensor_msgs.msg import JointState
from std_msgs.msg import Bool

parser=argparse.ArgumentParser();parser.add_argument('--air',action='store_true');parser.add_argument('--reverse',action='store_true');args=parser.parse_args()
out=Path('/tmp/robovigor-wheel-validation');out.mkdir(exist_ok=True)
label='air' if args.air else ('reverse' if args.reverse else 'ground');log=(out/(label+'.log')).open('w')
rclpy.init();node=rclpy.create_node('wheel_physics_probe')
odom=[];cloud=[];joints={}
def joint(msg):
 for i,name in enumerate(msg.name):
  joints[name]=(msg.position[i],msg.velocity[i] if i<len(msg.velocity) else 0.)
subs=[node.create_subscription(Odometry,'/odom',odom.append,50),
      node.create_subscription(PoseStamped,'/gimbal_pose',cloud.append,50),
      node.create_subscription(JointState,'/joint_states',joint,50)]
pub=node.create_publisher(Twist,'/cmd_vel',1);spin=node.create_publisher(Bool,'/spin_mode',1)
cmd=['ros2','launch','sentry_simulation','simulation.launch.py','gui:=false','rviz:=false']
if args.air:cmd+=['z:=3.0']
p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
def simtime():return odom[-1].header.stamp.sec+odom[-1].header.stamp.nanosec*1e-9
def pump(seconds,v=(0,0,0),hold=False):
 start=simtime();deadline=time.monotonic()+45
 while simtime()-start<seconds:
  m=Twist();m.linear.x,m.linear.y,m.angular.z=map(float,v)
  pub.publish(m);spin.publish(Bool(data=hold))
  if hold and cloud:
   records['max_gimbal_error']=max(records.get('max_gimbal_error',0),abs(math.atan2(math.sin(heading()-start_heading),math.cos(heading()-start_heading))))
  rclpy.spin_once(node,timeout_sec=.01)
  if time.monotonic()>deadline:raise RuntimeError('Simulation is too slow/stalled')
  assert p.poll() is None,'Launch stopped'
def snapshot():
 m=odom[-1];q=m.pose.pose.orientation
 return dict(t=simtime(),x=m.pose.pose.position.x,y=m.pose.pose.position.y,z=m.pose.pose.position.z,
  yaw=math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z)),
  vx=m.twist.twist.linear.x,vy=m.twist.twist.linear.y,wz=m.twist.twist.angular.z,
  wheels={k:v for k,v in joints.items() if k.startswith('wheel_')},
  max_roller_speed=max([abs(v[1]) for k,v in joints.items() if k.startswith('roller_')]+[0]))
records={}
def heading():
 q=cloud[-1].pose.orientation
 return math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))
try:
 deadline=time.monotonic()+40
 while (not odom or len(joints)<117) and time.monotonic()<deadline:
  rclpy.spin_once(node,timeout_sec=.1)
 assert odom and len(joints)>=117,('No actual joint state',len(joints))
 records['initial']=snapshot();print('initial',json.dumps(records['initial']),flush=True)
 if args.air:
  pump(.15,(.4,0,0));records['driven']=snapshot()
  assert abs(records['driven']['x']-records['initial']['x'])<.02,'Airborne motor translated vehicle'
  assert records['driven']['z']>.5
  assert max(abs(v[1]) for v in records['driven']['wheels'].values())>1
  print('PASS airborne: wheels spin; vehicle does not translate horizontally',flush=True)
 else:
  pump(.5);records['settled']=snapshot();print('settled',json.dumps(records['settled']),flush=True)
  pump(1.,(.8,0,0));records['forward']=snapshot();print('forward',json.dumps(records['forward']),flush=True)
  if args.reverse:
   pump(.5);pump(1.,(-.8,0,0));records['reverse']=snapshot()
   deadline=time.monotonic()+2.5
   while time.monotonic()<deadline:rclpy.spin_once(node,timeout_sec=.02)
   records['watchdog_stop']=snapshot()
   (out/(label+'.json')).write_text(json.dumps(records,indent=2)+'\n')
   assert records['reverse']['vx']<-.65
   assert abs(records['watchdog_stop']['vx'])<.02
   print('PASS reverse and watchdog: '+json.dumps(records),flush=True)
   raise SystemExit(0)
  pump(.5);pump(1.,(0,.8,0));records['lateral']=snapshot();print('lateral',json.dumps(records['lateral']),flush=True)
  pump(.5);start_heading=heading();pump(3.,(0,0,3.),True);records['spin']=snapshot();records['spin']['gimbal_error']=math.atan2(math.sin(heading()-start_heading),math.cos(heading()-start_heading));print('spin',json.dumps(records['spin']),flush=True)
  pump(1.);records['stopped']=snapshot();print('stopped',json.dumps(records['stopped']),flush=True)

 if not args.air:
  assert records['forward']['vx']>.65
  assert records['lateral']['vy']>.65
  assert records['spin']['wz']>2.6
  assert abs(records['spin']['gimbal_error'])<.05
  assert records['max_gimbal_error']<.05
  assert abs(records['stopped']['vx'])+abs(records['stopped']['vy'])<.02
  assert abs(records['stopped']['wz'])<.05
  print('PASS ground: forward, lateral, default gyro, gimbal hold, braking',flush=True)
 (out/(label+'.json')).write_text(json.dumps(records,indent=2)+'\n')
finally:
 pub.publish(Twist());spin.publish(Bool(data=False))
 if p.poll() is None:
  os.kill(p.pid,signal.SIGINT)
  try:p.wait(timeout=15)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=5)
 log.close();node.destroy_node();rclpy.shutdown()
