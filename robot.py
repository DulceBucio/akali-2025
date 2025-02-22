# Ultima modificación: 04/02/2025
# Cualquier cosa preguntenle a Dultez (No le sabe)

import wpilib
import wpilib.drive
import phoenix5 

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

        self.servo1 = wpilib.Servo(0)
        self.servo2 = wpilib.Servo(1)
        self.servo3 = wpilib.Servo(2)
        self.servo4 = wpilib.Servo(3)

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
        """This function is called periodically during teleoperated mode."""
        print("LeftY:", self.controller.getLeftY())
        print("RightX:", self.controller.getRightX())

        self.robotDrive.arcadeDrive(
            -self.controller.getLeftY(), -self.controller.getRightX()
        )


    # Mecanica esa rara que no le entiendo y de la cual no estoy segura :D

    # def teleopPeriodic(self):
    #     """This function is called periodically during teleoperated mode."""
    
    #     forward = -self.controller.getLeftY()  # Forward/backward movement
    #     turn = -self.controller.getRightX()  # Turning movement
    
    #     left_speed = forward + turn
    #     right_speed = forward - turn
    
    #     if turn > 0:  # Turning right
    #         right_speed *= 0.5  # Reduce right side speed
    #     elif turn < 0:  # Turning left
    #         left_speed *= 0.5  # Reduce left side speed

    #     self.leftDrive.set(left_speed)
    #     self.rightDrive.set(right_speed)

    #     # if self.controller.getAButton():
    #     #     self.servo.set(1.0)  
    #     # elif self.controller.getBButton():
    #     #     self.servo.set(0.0)  
    #     # else:
    #     #     self.servo.set(0.5) 


if __name__ == "__main__":
    wpilib.run(MyRobot)

