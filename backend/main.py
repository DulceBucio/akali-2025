import cv2
import numpy as np
from flask import Flask, Response, jsonify, request
from flask_socketio import SocketIO, emit
from Capture import Capture

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # Allow CORS if needed

# Initialize video capture
cap1 = Capture()
movement_command = "stop"  # Global variable to store the last command

color_lower = np.array([0, 100, 100])  # Red in HSV
color_upper = np.array([10, 255, 255])
densidad_umbral = 10  # Threshold for obstacle detection

# Function to process sections of the image (left, center, right)
def process_section(section):
    gray = cv2.cvtColor(section, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)

    kernel = np.ones((3, 3), np.uint8)
    dilated = cv2.dilate(edges, kernel, iterations=1)
    eroded = cv2.erode(dilated, kernel, iterations=1)
    closed = cv2.morphologyEx(eroded, cv2.MORPH_CLOSE, kernel)

    contornos, _ = cv2.findContours(closed.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return len(contornos)

# Function to generate movement command
def detect_obstacles_and_color(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)

    height, width = frame.shape[:2]
    center_x = width // 2
    left_region = edges[:, :center_x]
    right_region = edges[:, center_x:]

    left_intensity = np.sum(left_region)
    right_intensity = np.sum(right_region)
    threshold = 100000  # Adjust as needed

    if left_intensity < threshold and right_intensity < threshold:
        movement_command = 'forward'
    elif left_intensity > right_intensity:
        movement_command = 'right'
    else:
        movement_command = 'left'

    center_region = frame[height // 3: 2 * height // 3, center_x - 50:center_x + 50]
    hsv = cv2.cvtColor(center_region, cv2.COLOR_BGR2HSV)
    
    red_lower = np.array([0, 120, 70])
    red_upper = np.array([10, 255, 255])
    yellow_lower = np.array([25, 100, 100])
    yellow_upper = np.array([35, 255, 255])
    green_lower = np.array([50, 100, 100])
    green_upper = np.array([70, 255, 255])
    
    mask_red = cv2.inRange(hsv, red_lower, red_upper)
    mask_yellow = cv2.inRange(hsv, yellow_lower, yellow_upper)
    mask_green = cv2.inRange(hsv, green_lower, green_upper)

    if np.sum(mask_red) > 1000:
        movement_command = 'stop'
    elif np.sum(mask_yellow) > 1000:
        movement_command = 'stop'
    elif np.sum(mask_green) > 1000:
        movement_command = 'forward'

    return movement_command

# Function to generate video stream
def generate(capture):
    global movement_command  # Ensure updates affect the global variable

    while True:
        ret, frame = capture.get_frame()
        if ret:
            movement_command = detect_obstacles_and_color(frame)  # Update command

            # Emit updated movement command to WebSocket clients
            socketio.emit('movement_command', {'command': movement_command})
            print(movement_command)
            (flag, encodedImage) = cv2.imencode(".jpg", frame)
            if not flag:
                continue
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
                   bytearray(encodedImage) + b'\r\n')

@app.route("/video1")
def video1():
    return Response(generate(cap1),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/commands", methods=['POST'])
def send_commands():
    global movement_command

    data = request.json
    if not data or "command" not in data:
        return jsonify({"error": "Missing 'command' in request"}), 400

    movement_command = data["command"]
    socketio.emit('movement_command', {'command': movement_command})
    
    return jsonify({"status": "Command sent", "command": movement_command}), 200

@app.route("/commands", methods=['GET'])
def get_commands():
    return jsonify({'command': movement_command}), 200

@socketio.on('connect')
def handle_connect():
    print("Client connected") 

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")

if __name__ == '__main__':
    # REMOVE generate(cap1) here! It must be only used inside Response()
    socketio.run(app, host='0.0.0.0', port=8080, debug=False, use_reloader=False)