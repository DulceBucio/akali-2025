# Ultima modificación: 04/02/2025
# Cualquier cosa preguntenle a Dultez (No le sabe)

import wpilib
import wpilib.drive
import phoenix5 

servo_movement_exterior = 0
servo_movement_interior = 0

class MyRobot(wpilib.TimedRobot):
    def robotInit(self):
        """This function is called upon program startup and should be used for any initialization code."""

        self.leftDrive = phoenix5.WPI_VictorSPX(2)  # YA QUEDARON LOS IDS NO MOVER BYE
        self.rightDrive = phoenix5.WPI_VictorSPX(12)

        self.robotDrive = wpilib.drive.DifferentialDrive(self.leftDrive, self.rightDrive)
        self.controller = wpilib.XboxController(0)
        self.timer = wpilib.Timer()

        # Invert the right side if needed
        self.rightDrive.setInverted(True)

        self.servoLF = wpilib.Servo(0)
        self.servoLB = wpilib.Servo(1)
        self.servoRF = wpilib.Servo(2)
        self.servoRB = wpilib.Servo(8)

        # servos a su 0
        self.servoLF.set(0.5)
        self.servoLB.set(0.5)
        self.servoRF.set(0.5)
        self.servoRF.set(0.5)



    def autonomousInit(self):
        """This function is run once each time the robot enters autonomous mode."""
        self.timer.restart()

    def autonomousPeriodic(self):
        """This function is called periodically during autonomous."""
        if self.timer.get() < 2.0:
            self.leftDrive.set(0.5)
            self.rightDrive.set(0.5)
        else:
            self.robotDrive.stopMotor()  
    
    def teleopPeriodic(self):   
        forward = -self.controller.getLeftY()
        servo_movement_interior = max(0.2, min(self.controller.getRightX() * 0.5 + 0.5, 0.8))  # Scale -1 to 1 -> 0 to 1 sabe solo dios y yo sabemos pq esto funciona
        servo_movement_exterior = servo_movement_interior * 0.53
        opposite_servo_movement = 1 - servo_movement_interior
        opposite_servo_movement_ext = 1 - servo_movement_exterior
        

        self.leftDrive.set(forward)
        self.rightDrive.set(forward)

        # Set servo positions
        if(self.controller.getRightBumperButton()):
            self.servoLF.set(servo_movement_interior)  
            self.servoRF.set(servo_movement_exterior)
            self.servoLB.set(opposite_servo_movement)  
            self.servoRB.set(opposite_servo_movement_ext)
        elif (self.controller.getLeftBumperButton()):
            self.servoLF.set(servo_movement_exterior)  
            self.servoRF.set(servo_movement_interior)
            self.servoLB.set(opposite_servo_movement_ext)  
            self.servoRB.set(opposite_servo_movement)
        elif (self.controller.getBButton()):
            self.servoLF.set(0.5)
            self.servoLB.set(0.5)
            self.servoRF.set(0.5)
            self.servoRF.set(0.5)   




if __name__ == "__main__":
    wpilib.run(MyRobot)
