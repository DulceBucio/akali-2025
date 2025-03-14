import cv2
import numpy as np
import time
from flask import Flask, Response, jsonify, request
from flask_socketio import SocketIO, emit
from Capture import Capture

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize video capture
cap1 = Capture()
movement_command = "stop"  # Global variable to store the last command

# ======================================================
# COLOR DETECTION PARAMETERS
# ======================================================
# Red (two ranges to cover the full spectrum)
red_lower1 = np.array([0, 120, 70], np.uint8)
red_upper1 = np.array([10, 255, 255], np.uint8)
red_lower2 = np.array([170, 120, 70], np.uint8)
red_upper2 = np.array([180, 255, 255], np.uint8)

# Yellow
yellow_lower = np.array([20, 100, 100], np.uint8)
yellow_upper = np.array([30, 255, 255], np.uint8)

# Green
green_lower = np.array([35, 100, 100], np.uint8)
green_upper = np.array([85, 255, 255], np.uint8)

# Canny edge detection parameters
CANNY_LOWER = 30
CANNY_UPPER = 100

# ======================================================
# GLOBAL STATE VARIABLES
# ======================================================
# Color detection states and timing
red_detected = False
red_start_time = None

yellow_detected = False
yellow_start_time = None

green_detected = False
green_start_time = None

# Main operation states
OPERACION_NORMAL = "OPERACION_NORMAL"
ESPERANDO_VERDE = "ESPERANDO_VERDE"

current_state = OPERACION_NORMAL
turning = False

# ======================================================
# EDGE DETECTION FUNCTIONS
# ======================================================
def detect_edges(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, CANNY_LOWER, CANNY_UPPER)
    return edges

def analyze_edges(edges):
    """
    Returns which section (LEFT, CENTER, RIGHT) has the fewest edges,
    or 'NO_EDGES' if no edges are detected.
    """
    height, width = edges.shape
    third = width // 3

    left_section = edges[:, 0:third]
    center_section = edges[:, third:2*third]
    right_section = edges[:, 2*third:width]

    # Count white pixels (edges) in each section
    left_count = cv2.countNonZero(left_section)
    center_count = cv2.countNonZero(center_section)
    right_count = cv2.countNonZero(right_section)

    # If no edges in any section, indicate "NO_EDGES"
    total_edges = left_count + center_count + right_count
    if total_edges == 0:
        return "NO_EDGES"

    # Find the section with the least edges
    values = {
        "LEFT": left_count,
        "CENTER": center_count,
        "RIGHT": right_count
    }
    direction = min(values, key=values.get)
    return direction

# ======================================================
# COLOR DETECTION FUNCTIONS
# ======================================================
def detect_center_colors(frame):
    """
    Analyze the center portion of the frame for colors.
    Returns (is_red, is_yellow, is_green) as booleans.
    """
    height, width, _ = frame.shape
    third = width // 3

    # Take only the center portion of the frame
    center_frame = frame[:, third:2*third]

    # Convert to HSV
    hsv_center = cv2.cvtColor(center_frame, cv2.COLOR_BGR2HSV)

    # Red masks (two ranges)
    mask_red1 = cv2.inRange(hsv_center, red_lower1, red_upper1)
    mask_red2 = cv2.inRange(hsv_center, red_lower2, red_upper2)
    red_mask = cv2.add(mask_red1, mask_red2)
    red_count = cv2.countNonZero(red_mask)

    # Yellow mask
    yellow_mask = cv2.inRange(hsv_center, yellow_lower, yellow_upper)
    yellow_count = cv2.countNonZero(yellow_mask)

    # Green mask
    green_mask = cv2.inRange(hsv_center, green_lower, green_upper)
    green_count = cv2.countNonZero(green_mask)

    # Calculate total pixels in center section
    total_pixels = center_frame.shape[0] * center_frame.shape[1]

    # Determine if >50% of the center section is a specific color
    red_percentage = red_count / total_pixels
    yellow_percentage = yellow_count / total_pixels
    green_percentage = green_count / total_pixels

    is_red = (red_percentage > 0.5)
    is_yellow = (yellow_percentage > 0.5)
    is_green = (green_percentage > 0.5)

    return is_red, is_yellow, is_green

# ======================================================
# STATE MANAGEMENT FUNCTIONS
# ======================================================
def handle_red_yellow(red_center, yellow_center, current_time):
    """
    Handle red and yellow detection logic in NORMAL_OPERATION state
    """
    global red_detected, red_start_time
    global yellow_detected, yellow_start_time

    # Red handling
    if red_center:
        if not red_detected:
            red_detected = True
            red_start_time = current_time
        elif (current_time - red_start_time) >= 2.0:
            # Switch to WAITING_FOR_GREEN state
            return "RED_STOP"
    else:
        red_detected = False
        red_start_time = None

    # Yellow handling
    if yellow_center:
        if not yellow_detected:
            yellow_detected = True
            yellow_start_time = current_time
        elif (current_time - yellow_start_time) >= 1.0:
            return "YELLOW_STOP"
    else:
        yellow_detected = False
        yellow_start_time = None

    return "NO_COLOR_STOP"

def handle_green(green_center, current_time):
    """
    Handle green detection logic in WAITING_FOR_GREEN state
    """
    global green_detected, green_start_time

    if green_center:
        if not green_detected:
            green_detected = True
            green_start_time = current_time
        elif (current_time - green_start_time) >= 2.0:
            # Green detected for 2+ seconds
            return "GREEN_READY"
    else:
        green_detected = False
        green_start_time = None

    return "WAITING_GREEN"

def state_logic(red_center, yellow_center, green_center, current_time):
    """
    Main state machine logic
    """
    global current_state

    if current_state == OPERACION_NORMAL:
        # Red and yellow logic
        color_state = handle_red_yellow(red_center, yellow_center, current_time)

        if color_state == "RED_STOP":
            current_state = ESPERANDO_VERDE
            print("State -> WAITING_FOR_GREEN (motors OFF).")
            return "RED_WAIT"
        else:
            return color_state  # "NO_COLOR_STOP" or "YELLOW_STOP"

    elif current_state == ESPERANDO_VERDE:
        # Only care about green detection
        green_state = handle_green(green_center, current_time)
        if green_state == "GREEN_READY":
            print("Green detected for 2+ seconds -> Returning to NORMAL_OPERATION.")
            current_state = OPERACION_NORMAL
        return "WAITING_FOR_GREEN"

# ======================================================
# DETERMINE MOVEMENT COMMAND
# ======================================================
def determine_movement(frame):
    global current_state, turning, movement_command

    # Detect edges for obstacle avoidance
    edges = detect_edges(frame)
    
    # Detect colors in the center section
    red_center, yellow_center, green_center = detect_center_colors(frame)
    current_time = time.time()
    
    # Get state logic
    state = state_logic(red_center, yellow_center, green_center, current_time)
    
    # Determine movement based on state
    if current_state == OPERACION_NORMAL:
        if state == "YELLOW_STOP":
            print("Stopping for YELLOW signal (present for 1+ seconds).")
            movement_command = "stop"
            
        elif state == "RED_WAIT":
            # Switched to WAITING_FOR_GREEN state (motors OFF)
            movement_command = "stop"
            
        else:
            # Normal obstacle avoidance logic
            edge_direction = analyze_edges(edges)
            
            if turning:
                if edge_direction != "NO_EDGES":
                    turning = False
                    print("Path found. Stopping turn.")
                else:
                    print("Turning to find a path...")
                    movement_command = "right"  # Default turn direction
            else:
                if edge_direction == "NO_EDGES":
                    turning = True
                    print("Obstacle detected - STARTING TURN.")
                    movement_command = "right"
                else:
                    # Move towards the direction with fewer edges
                    if edge_direction == "LEFT":
                        print("Moving left")
                        movement_command = "left"
                    elif edge_direction == "RIGHT":
                        print("Moving right")
                        movement_command = "right"
                    else:  # CENTER
                        print("Moving forward")
                        movement_command = "forward"
    
    elif current_state == ESPERANDO_VERDE:
        # Waiting for green, keep motors off
        print("Waiting for green signal for 2+ seconds... (motors OFF)")
        movement_command = "stop"
    
    return movement_command

# ======================================================
# VIDEO STREAMING FUNCTION
# ======================================================
def generate(capture):
    global movement_command

    while True:
        ret, frame = capture.get_frame()
        if ret:
            # Process frame and determine movement
            movement_command = determine_movement(frame)

            # Emit updated movement command to WebSocket clients
            socketio.emit('movement_command', {'command': movement_command})
            print(f"Movement command: {movement_command}")
            
            # Encode frame for streaming
            (flag, encodedImage) = cv2.imencode(".jpg", frame)
            if not flag:
                continue
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
                   bytearray(encodedImage) + b'\r\n')

# ======================================================
# ROUTES AND SOCKET HANDLERS
# ======================================================
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

# ======================================================
# MAIN EXECUTION
# ======================================================
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8080, debug=False, use_reloader=False)