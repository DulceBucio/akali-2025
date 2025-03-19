import wpilib
import wpilib.drive
import phoenix5
import threading
import asyncio
import websockets
import json
import requests
import time
SERVER_URL = "http://10.59.48.227:8080/commands"

def fetch_commands():
    """Fetch movement commands from the HTTP server."""
    try:
        response = requests.get(SERVER_URL, timeout=2)
        if response.status_code == 200:
            data = response.json()
            return data.get("command", "stop")
    except requests.RequestException as e:
        print(f"Failed to fetch command: {e}")
    return "stop"

def command_listener(robot):
    """Continuously fetch commands and update the robot."""
    while True:
        robot.current_command = fetch_commands()
        print("Received command:", robot.current_command)
        time.sleep(0.5)  # Adjust polling rate as needed

class MyRobot(wpilib.TimedRobot):
    def robotInit(self):
        self.leftDrive = phoenix5.WPI_VictorSPX(2)
        self.rightDrive = phoenix5.WPI_VictorSPX(12)
        self.robotDrive = wpilib.drive.DifferentialDrive(self.leftDrive, self.rightDrive)
        self.controller = wpilib.XboxController(0)
        self.timer = wpilib.Timer()
        self.rightDrive.setInverted(True)

        self.servoLF = wpilib.Servo(0)
        self.servoLB = wpilib.Servo(1)
        self.servoRF = wpilib.Servo(2)
        self.servoRB = wpilib.Servo(8)

        self.servoLF.set(0.5)
        self.servoLB.set(0.5)
        self.servoRF.set(0.5)
        self.servoRB.set(0.5)

        self.current_command = "stop"

        # Start a separate thread for fetching commands
        self.command_thread = threading.Thread(target=command_listener, args=(self,))
        self.command_thread.daemon = True
        self.command_thread.start()

    async def listen_for_commands(self):
        """Listen for movement commands from the WebSocket server."""
        async with websockets.connect(SERVER_URL) as websocket:
            print("Connected to the server")

            while True:
                message = await websocket.recv()

                # Parse the message (assuming it's in JSON format)
                try:
                    data = json.loads(message)
                    if "command" in data:
                        self.handle_movement_command(data)
                except json.JSONDecodeError:
                    print(f"Received non-JSON message: {message}")

    def handle_movement_command(self, data):
        """Handle the received movement command."""
        self.current_command = data.get('command', 'stop')
        print("Received movement command:", self.current_command)

    def autonomousInit(self):
        self.timer.restart()

    def autonomousPeriodic(self):
        if self.current_command == "forward":
            print("Moving forward")
            self.servoLF.set(0.5)
            self.servoRF.set(0.5)
            self.servoLB.set(0.5)
            self.servoRB.set(0.5)
            self.leftDrive.set(0.5)
            self.rightDrive.set(0.5)
        elif self.current_command == "left":
            print("Turning left")
            self.leftDrive.set(0.3)
            self.rightDrive.set(0.3)
            
            
            self.servoLF.set(0.3)
            self.servoRF.set(0.3)
            self.servoLB.set(0.7)
            self.servoRB.set(0.7)
        elif self.current_command == "right":
            print("Turning right")
            self.leftDrive.set(0.3)
            self.rightDrive.set(0.3)

            self.servoLF.set(0.7)
            self.servoRF.set(0.7)
            self.servoLB.set(0.3)
            self.servoRB.set(0.3)

        elif self.current_command == "backward":
            self.servoLF.set(0.7)
            self.servoRF.set(0.7)
            self.servoLB.set(0.3)
            self.servoRB.set(0.3)
            self.leftDrive.set(-0.5)
            self.rightDrive.set(-0.5)
            # time.sleep(10)
        else:  # "stop" or unknown command
            print("Stopping")
            self.robotDrive.stopMotor()

    def teleopPeriodic(self):
        forward = -self.controller.getLeftY()
        servo_movement = max(0.2, min(self.controller.getRightX() * 0.5 + 0.5, 0.8))  # Scale -1 to 1 -> 0 to 1
        opposite_servo_movement = 1 - servo_movement

        print("Servo Movement (Front):", servo_movement)
        print("Servo Movement (Back):", opposite_servo_movement)

        self.leftDrive.set(forward)
        self.rightDrive.set(forward)

        self.servoLF.set(servo_movement)
        self.servoRF.set(servo_movement)
        self.servoLB.set(opposite_servo_movement)
        self.servoRB.set(opposite_servo_movement)

if __name__ == "__main__":
    wpilib.run(MyRobot)
