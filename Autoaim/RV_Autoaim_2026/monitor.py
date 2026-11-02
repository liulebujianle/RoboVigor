import cv2
import time
import threading
from flask import Flask, Response, render_template_string


class Monitor:
    def __init__(self, enable_draw=False, enable_web=False, host="0.0.0.0", port=5000, jpeg_quality=80):
        self.enable_draw = enable_draw
        self.enable_web = enable_web
        self.host = host
        self.port = port
        self.jpeg_quality = int(max(10, min(jpeg_quality, 100)))

        self.latest_frame = None
        self.lock = threading.Lock()

        self.app = None
        self.web_thread = None

        if self.enable_web:
            self.app = Flask(__name__)
            self._setup_routes()

    # ============================
    # Flask 路由
    # ============================
    def _setup_routes(self):
        @self.app.route('/')
        def index():
            html = """
            <!doctype html>
            <html>
            <head>
                <title>RoboMaster Detection</title>
            </head>
            <body>
                <h2>Live Detection</h2>
                <img src="/video_feed" width="1280" height="1024">
            </body>
            </html>
            """
            return render_template_string(html)

        @self.app.route('/video_feed')
        def video_feed():
            return Response(
                self.gen_frames(),
                mimetype='multipart/x-mixed-replace; boundary=frame'
            )

    # ============================
    # MJPEG 推流
    # ============================
    def gen_frames(self):
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality]

        while True:
            with self.lock:
                if self.latest_frame is None:
                    frame = None
                else:
                    frame = self.latest_frame.copy()

            if frame is None:
                time.sleep(0.01)
                continue

            ret, jpeg = cv2.imencode('.jpg', frame, encode_param)
            if not ret:
                continue

            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' +
                jpeg.tobytes() +
                b'\r\n'
            )

    # ============================
    # 更新最新帧
    # ============================
    def update_frame(self, frame):
        if not self.enable_web:
            return

        with self.lock:
            self.latest_frame = frame

    # ============================
    # 绘图 + 推流
    # ============================
    def render(self, frame, boxes=None, pred_point=None, yaw_error=None, pitch_error=None, distance=None, fire_command=None, best_target=None):
        if not self.enable_draw and not self.enable_web:
            return None

        annotated = frame.copy()

        # 画框
        if boxes is not None:
            for box in boxes:
                x1, y1, x2, y2 = map(int, box)
                cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # 预测点
        if pred_point is not None:
            px, py = pred_point
            cv2.circle(annotated, (int(px), int(py)), 6, (0, 0, 255), -1)

        # None 表示不显示；0 和 False 仍然是有效显示值。
        green = (0, 255, 0)
        labels = [
            ("Target locked" if best_target is not None else "No target",
             green if best_target is not None else (0, 255, 255)),
        ]
        if yaw_error is not None:
            labels.append((f"Yaw_error: {yaw_error:.1f} deg", green))
        if pitch_error is not None:
            labels.append((f"Pitch_error: {pitch_error:.1f} deg", green))
        if distance is not None:
            labels.append((f"Distance: {distance:.0f} mm", green))
        if fire_command is not None:
            labels.append((f"Fire Command: {fire_command}", green))

        for row, (text, color) in enumerate(labels, start=1):
            cv2.putText(annotated, text, (10, row * 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        if self.enable_web:
            self.update_frame(annotated)

        return annotated if self.enable_draw else None

    # ============================
    # 启动 Flask
    # ============================
    def run(self):
        if not self.enable_web:
            return
        self.app.run(host=self.host, port=self.port, threaded=True, debug=False)

    def start(self):
        if not self.enable_web:
            return

        if self.web_thread is None or not self.web_thread.is_alive():
            self.web_thread = threading.Thread(target=self.run, daemon=True)
            self.web_thread.start()