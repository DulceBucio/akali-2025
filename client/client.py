# Ultima modificación: 07/02/2025

import wpilib
import wpilib.drive
import phoenix5
import threading
import socketio

class MyRobot(wpilib.TimedRobot):
    def robotInit(self):
        """This function is called upon program startup and should be used for any initialization code."""

        self.leftDrive = phoenix5.WPI_VictorSPX(2)  # YA QUEDARON LOS IDS NO MOVER BYE
        self.rightDrive = phoenix5.WPI_VictorSPX(12)

        self.robotDrive = wpilib.drive.DifferentialDrive(self.leftDrive, self.rightDrive)
        self.controller = wpilib.XboxController(0)
        self.timer = wpilib.Timer()
        self.rightDrive.setInverted(True)

        self.servoLF = wpilib.Servo(0)
        self.servoLB = wpilib.Servo(1)
        self.servoRF = wpilib.Servo(2)
        self.servoRB = wpilib.Servo(8)

        # servos a su 0
        self.servoLF.set(0.5)
        self.servoLB.set(0.5)
        self.servoRF.set(0.5)
        self.servoRB.set(0.5)


        self.sio = socketio.Client()
        self.current_command = "stop" 

        self.sio.on('movement_command', self.handle_movement_command)

        try:
            self.sio.connect('http://10.59.48.227:8080') 
        except Exception as e:
            print("Error connecting to WebSocket server:", e)

        # Run the WebSocket listener in a separate thread
        threading.Thread(target=self.sio.wait, daemon=True).start()

    def handle_movement_command(self, data):
        self.current_command = data.get('command', 'stop')
        print("Received movement command:", self.current_command)

    def autonomousInit(self):
        self.timer.restart()

    def autonomousPeriodic(self):
        if self.current_command == "forward":
            self.leftDrive.set(0.5)
            self.rightDrive.set(0.5)
        elif self.current_command == "left":
            self.leftDrive.set(-0.3)
            self.rightDrive.set(0.3)
        elif self.current_command == "right":
            self.leftDrive.set(0.3)
            self.rightDrive.set(-0.3)
        else:  # "stop" or unknown command
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
