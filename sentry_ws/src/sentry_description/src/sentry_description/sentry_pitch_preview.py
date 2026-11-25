"""在 RViz 车体旁显示独立的俯仰角示意表，角度单位为度。"""
import math

import rclpy
from geometry_msgs.msg import Point
from rcl_interfaces.msg import SetParametersResult
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from visualization_msgs.msg import Marker, MarkerArray


def dial_point(degrees, radius):
    angle = math.radians(degrees)
    return Point(x=radius * math.cos(angle), z=radius * math.sin(angle))


def dial_marker(index, kind, rgb):
    marker = Marker()
    marker.header.frame_id = 'base_link'
    marker.frame_locked = True
    marker.ns, marker.id, marker.type = 'pitch_preview', index, kind
    marker.pose.position = Point(y=-0.44, z=0.47)
    marker.pose.orientation.w = 1.0
    marker.color.r, marker.color.g, marker.color.b = rgb
    marker.color.a = 1.0
    return marker


def make_gauge(degrees):
    """灰线是相对车体的水平线，蓝线向上偏转时角度为正。"""
    scale = dial_marker(0, Marker.LINE_LIST, (0.78, 0.78, 0.78))
    scale.scale.x = 0.006
    scale.points = [Point(x=-0.035), Point(x=0.20)]
    for tick in range(-90, 91, 15):
        scale.points.extend([dial_point(tick, 0.17), dial_point(tick, 0.19)])

    needle = dial_marker(1, Marker.LINE_STRIP, (0.10, 0.75, 1.00))
    needle.scale.x = 0.014
    needle.points = [Point(), dial_point(degrees, 0.165)]

    label = dial_marker(2, Marker.TEXT_VIEW_FACING, (1.0, 1.0, 1.0))
    label.pose.position.z += 0.25
    label.scale.z = 0.065
    label.text = f'Pitch {degrees:+.1f} deg'
    return MarkerArray(markers=[scale, needle, label])


class PitchPreview(Node):
    def __init__(self):
        super().__init__('sentry_pitch_preview')
        self.add_on_set_parameters_callback(self.validate)
        self.declare_parameter('angle_deg', 0.0)
        qos = QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE,
                         durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.publisher = self.create_publisher(MarkerArray, '/sentry_description/pitch_preview', qos)
        self.last_angle = None
        self.update_display()
        self.create_timer(0.2, self.update_display)

    @staticmethod
    def validate(parameters):
        for param in parameters:
            if param.name == 'angle_deg' and (
                param.type_ != Parameter.Type.DOUBLE or not -90.0 <= param.value <= 90.0
            ):
                return SetParametersResult(successful=False, reason='angle_deg must be a number from -90.0 to 90.0')
        return SetParametersResult(successful=True)

    def update_display(self):
        degrees = self.get_parameter('angle_deg').value
        if degrees != self.last_angle:
            self.publisher.publish(make_gauge(degrees))
            self.last_angle = degrees


def main(args=None):
    rclpy.init(args=args)
    node = PitchPreview()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
