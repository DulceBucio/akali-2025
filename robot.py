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

        self.leftDrive.setSafetyEnabled(False)
        self.rightDrive.setSafetyEnabled(False)


        self.robotDrive = wpilib.drive.DifferentialDrive(self.leftDrive, self.rightDrive)
        self.controller = wpilib.XboxController(0)
        self.timer = wpilib.Timer()

        # Invert the right side if needed
        self.rightDrive.setInverted(True)

        self.servoLF = wpilib.Servo(0)
        self.servoLB = wpilib.Servo(1)
        self.servoRF = wpilib.Servo(2)
        self.servoRB = wpilib.Servo(3)

        self.servo_movement_right = 0.5  
        self.servo_movement_left = 0.5  

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

    # def teleopPeriodic(self):   
    #     # print("LeftY:", self.controller.getLeftY())
    #     # print("RightX:", self.controller.getRightX())

    #     servo_movement = self.controller.getRightX() + 0.5 # No remapping, keep -1 to 1
    #     print("JOYSTICK:", self.controller.getRightX)
    #     print(servo_movement)
    #     opposite_servo_movement = 0.5 - servo_movement
    #     print(opposite_servo_movement)


    #     self.servoLB.set(0.5)
    #     self.servoLF.set(0.5)
    #     self.servoRB.set(0.5)
    #     self.servoRF.set(0.5)
    #     self.robotDrive.arcadeDrive(
    #         -self.controller.getLeftY(), -self.controller.getRightX()
    #     )
    #     self.servoLF.set(servo_movement) # Los front van hacia 1 !!
    #     self.servoLB.set(opposite_servo_movement)
    #     self.servoRF.set(servo_movement)
    #     self.servoRB.set(opposite_servo_movement)
    
    def teleopPeriodic(self):   
        forward = -self.controller.getLeftY()
        # servo_movement = self.controller.getRightX() * 0.5 + 0.5  # Scale -1 to 1 -> 0 to 1 sabe
        # opposite_servo_movement = 1 - servo_movement  

        # print("Servo Movement (Front):", servo_movement)
        # print("Servo Movement (Back):", opposite_servo_movement)

        self.leftDrive.set(forward)
        self.rightDrive.set(forward)
        
        # LLANTA DERECHA
        if self.controller.getRightBumper():
            self.servo_movement_right += 0.01  # Small increments for smooth change
        elif self.controller.getXButton():
            self.servo_movement_right -= 0.01
        # IZQ
        elif self.controller.getLeftBumper():
            self.servo_movement_left -= 0.01
        elif self.controller.getBButton():
            self.servo_movement_left += 0.01

        # Ensure servo_movement stays in the valid range (0.0 to 1.0)
        self.servo_movement_left = max(0.0, min(1.0, self.servo_movement_left))
        self.servo_movement_right = max(0.0, min(1.0, self.servo_movement_right))

        # print("Servo Movement:", self.servo_movement)

        self.servoLF.set(self.servo_movement_left)
        self.servoRF.set(self.servo_movement_right)

        # print(self.servo_movement)
        # # Set servo positions
        # self.servoLF.set(self.servo_movement)  # 0.5 to 1
        # self.servoRF.set(self.servo_movement)
        #self.servoLB.set(opposite_servo_movement)  # 0.5 to 0
        #self.servoRB.set(opposite_servo_movement)



if __name__ == "__main__":
    wpilib.run(MyRobot)

