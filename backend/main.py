import cv2
import numpy as np
import time
from flask import Flask, Response
from flask_socketio import SocketIO, emit
from Capture import Capture

app = Flask(__name__)
socketio = SocketIO(app)

cap1 = Capture()

color_lower = np.array([0, 100, 100])  
color_upper = np.array([10, 255, 255])
densidad_umbral = 10  

def process_section(section):
    gray = cv2.cvtColor(section, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)

    kernel = np.ones((3, 3), np.uint8)
    dilated = cv2.dilate(edges, kernel, iterations=1)
    eroded = cv2.erode(dilated, kernel, iterations=1)
    closed = cv2.morphologyEx(eroded, cv2.MORPH_CLOSE, kernel)

    contornos, _ = cv2.findContours(closed.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(section, contornos, -1, (0, 0, 255), 2)
    return len(contornos)

def detect_color(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, color_lower, color_upper)
    contornos, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    area_total = sum(cv2.contourArea(cnt) for cnt in contornos)
    return area_total > 3000  

def process_frame_and_generate_command(frame):
    roi_width = 400
    roi_height = 300
    height, width, _ = frame.shape

    x_start = (width - roi_width) // 2
    y_start = (height - roi_height) // 2
    x_end = x_start + roi_width
    y_end = y_start + roi_height

    roi_frame = frame[y_start:y_end, x_start:x_end]
    third_width = roi_width // 3
    left_section = roi_frame[:, :third_width]
    middle_section = roi_frame[:, third_width:2 * third_width]
    right_section = roi_frame[:, 2 * third_width:]

    left_count = process_section(left_section)
    center_count = process_section(middle_section)
    right_count = process_section(right_section)

    if max(left_count, center_count, right_count) > densidad_umbral:
        return 'stop'
    
    if left_count < center_count and left_count < right_count:
        return 'left'
    elif center_count <= left_count and center_count <= right_count:
        return 'forward'
    elif right_count < left_count and right_count < center_count:
        return 'right'
    
    return 'stop'

def generate(capture):
    while True:
        ret, frame = capture.get_frame()
        if ret:
            movement_command = process_frame_and_generate_command(frame)

            socketio.emit('movement_command', {'command': movement_command})

            (flag, encodedImage) = cv2.imencode(".jpg", frame)
            if not flag:
                continue
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
                   bytearray(encodedImage) + b'\r\n')

@app.route("/video1")
def video1():
    return Response(generate(cap1),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


@socketio.on('connect')
def handle_connect():
    print("Client connected")

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8080, debug=False, use_reloader=False)