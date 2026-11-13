"""ROS/Qt independent FPS pose, image freshness and translation policy."""
import math


def angle(value):
    return math.atan2(math.sin(value), math.cos(value))


def image_layout(width, height, encoding, step, size):
    """Validate byte layout including ROS per-row padding."""
    channels = {'rgb8': 3, 'bgr8': 3, 'rgba8': 4}.get(encoding)
    if (channels is None or width <= 0 or height <= 0
            or step < width * channels or size < step * height):
        raise ValueError('Unsupported or truncated FPS image')
    return channels, step


class ViewState:
    def __init__(self, timeout=.5):
        self.timeout = timeout
        self.yaw = self.pitch = 0.
        self.target_yaw = self.target_pitch = None
        self.last_pose = self.last_image = self.image_key = None

    def pose(self, quaternion, frame, now):
        if frame != 'world' or not all(math.isfinite(v) for v in quaternion):
            return False
        norm = math.sqrt(sum(v * v for v in quaternion))
        if norm < 1e-9 or not math.isfinite(norm):
            return False
        x, y, z, w = (v / norm for v in quaternion)
        self.yaw = math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))
        self.pitch = math.asin(max(-1., min(1., 2 * (w * y - z * x))))
        self.last_pose = now
        if self.target_yaw is None:
            self.sync_target()
        return True

    def sync_target(self):
        self.target_yaw = self.yaw
        self.target_pitch = max(-math.pi / 3, min(math.pi / 3, self.pitch))

    def image(self, key, now):
        # Only a newly received frame renews this monotonic watchdog. Never
        # compare a simulated header time to wall/monotonic time.
        if key != self.image_key:
            self.image_key, self.last_image = key, now

    def ready(self, now):
        return all(stamp is not None and 0 <= now - stamp < self.timeout
                   for stamp in (self.last_pose, self.last_image))

    def mouse(self, dx, dy, sensitivity):
        if self.target_yaw is None or not all(math.isfinite(v) for v in (dx, dy, sensitivity)):
            return
        self.target_yaw = angle(self.target_yaw - dx * sensitivity)
        self.target_pitch = max(-math.pi / 3, min(math.pi / 3,
                                               self.target_pitch + dy * sensitivity))


class ViewMotion:
    """Translate along measured view heading; release line lock while steering."""
    def __init__(self):
        self.reset()

    def reset(self):
        self.origin = self.direction = self.previous_yaw = None

    def command(self, forward, left, view_yaw, body_yaw, position, steering):
        c, s = math.cos(view_yaw), math.sin(view_yaw)
        vx, vy = c * forward - s * left, s * forward + c * left
        moving = math.hypot(vx, vy) > 1e-6
        turning = (self.previous_yaw is not None
                   and abs(angle(view_yaw - self.previous_yaw)) > 1e-4)
        self.previous_yaw = view_yaw
        if not moving:
            self.origin = self.direction = None
            return 0., 0.
        speed = math.hypot(vx, vy)
        direction = vx / speed, vy / speed
        changed = (self.direction is not None and
                   sum(a * b for a, b in zip(direction, self.direction)) < .999)
        if steering or turning or changed or self.origin is None:
            self.origin, self.direction = position, direction
        if not (steering or turning):
            nx, ny = -self.direction[1], self.direction[0]
            error = (position[0] - self.origin[0]) * nx + (position[1] - self.origin[1]) * ny
            correction = max(-.25, min(.25, -6. * error))
            vx, vy = vx + nx * correction, vy + ny * correction
        c, s = math.cos(body_yaw), math.sin(body_yaw)
        return c * vx + s * vy, -s * vx + c * vy
