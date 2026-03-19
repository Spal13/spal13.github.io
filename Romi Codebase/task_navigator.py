from driver_motor   import driver_motor
from driver_encoder import driver_encoder
from driver_control import driver_control
from driver_IR      import driver_IR
from driver_bump    import driver_bump

from task_share     import Share, Queue
from utime          import ticks_us, ticks_diff
import micropython
from pyb import Pin
import math
from ulab import numpy as np
from gc             import collect

pi = math.pi

S0 = micropython.const(0) # State 0 - initialiation
S1  = micropython.const(1) # state 1
S2  = micropython.const(2)
S3  = micropython.const(3)
S4  = micropython.const(4)
S5  = micropython.const(5)
S6  = micropython.const(6)
S7  = micropython.const(7)
S8  = micropython.const(8)
S9  = micropython.const(9)
S10  = micropython.const(10)
S11  = micropython.const(11)
S12  = micropython.const(12)

class task_navigator:

    def __init__(self, leftEncoder, rightEncoder, leftMotor, rightMotor, xShare, yShare, yawShare, homedShare, serialDriver):

        self._state: int = S0    # The present state of the task

        self._leftEncoder    = leftEncoder
        self._leftMotor      = leftMotor

        self._leftController = driver_control()
        self._leftController.set_kp(0.05)
        self._leftController.set_ki(1.2)

        self._rightEncoder    = rightEncoder
        self._rightMotor      = rightMotor

        self._rightController = driver_control()
        self._rightController.set_kp(0.05)
        self._rightController.set_ki(1.2)

        # line following PID controller
        self._lineController = driver_control() # line PID controller
        self._lineController.set_kp(35) #30
        self._lineController.set_ki(20) #20

        # waypoint following PID controller
        self._waypointController = driver_control() # waypoint yaw PID controller
        self._waypointController.set_kp(60)
        self._waypointController.set_ki(5)

        self._xShare = xShare
        self._yShare = yShare
        self._yawShare = yawShare
        self._homedShare = homedShare

        self._bumpDriver = driver_bump("PC4","PH0")
        self._serialDriver = serialDriver

        # IR sensor driver
        self._IR_driver = driver_IR(['A0','A1','A2','A3', 'A4', 'A5', 'C3', 'C2', 'C5'], self._serialDriver)

        self._s2start = 0
        self._s10start = 0

        self._setpoint = 200 # speed

        self._lastAtanAng = 0.0
        self._trueNecessaryYaw = 0.0

        self._leftStartPos = 0.0
        self._rightStartPos = 0.0
        self._startTime = 0.0
        self._endTime = 0.0

        
    def run(self):
        '''
        Runs one iteration of the task
        '''
        
        while True:
            collect()
            if self._state == S0: # Init state
                if self._homedShare.get() == True: # wait until healthy homed state
                    # reset encoders and enable motors
                    self._rightController.reset()
                    self._leftController.reset()
                    self._lineController.reset()

                    self._leftEncoder.zero()
                    self._rightEncoder.zero()

                    self._leftMotor.enable()
                    self._rightMotor.enable()

                    self._xShare.put(100.0)
                    self._yShare.put(800.0)
                    self._yawShare.put(0.0)

                    self._setpoint = 200

                    self._serialDriver.send("x",self._xShare.get())
                    self._serialDriver.send("y",self._yShare.get())
                    self._serialDriver.send("yaw",self._yawShare.get())

                    self._IR_driver.get_centroid()

                    if self._serialDriver.read() == 'r':
                        print("STARTING")
                        self._startTime = ticks_us()
                        self._state = S1
                        
                        #self._state = S2# TEMPORARY - JUMP RIGHT TO S2
                        self._waypointController.reset()
                        self._s2start = ticks_us()
                
            elif self._state == S1: # Straight line follow

                line_error = 0 - self._IR_driver.get_centroid()
                line_adjustment = self._lineController.update(line_error)

                if self._xShare.get() < 200:
                    self._setpoint = (self._xShare.get() * 4) - 200
                elif self._xShare.get() > 200 and self._xShare.get() < 1350:
                    self._setpoint = 600
                elif self._xShare.get() > 1350 and self._xShare.get() < 1475:
                    self._setpoint = (self._xShare.get() * -4) + 6000
                else:
                    self._setpoint = 100


                Rsetpoint = self._setpoint + line_adjustment
                Lsetpoint = self._setpoint - line_adjustment

                self._rightEncoder.update()
                Rvel = self._rightEncoder.get_velocity()
                Routput = self._rightController.update(Rsetpoint - Rvel)
                self._rightMotor.set_effort(Routput)

                self._leftEncoder.update()
                Lvel = self._leftEncoder.get_velocity()
                Loutput = self._leftController.update(Lsetpoint - Lvel)
                self._leftMotor.set_effort(Loutput)

                self._serialDriver.send("x",self._xShare.get())
                self._serialDriver.send("y",self._yShare.get())
                self._serialDriver.send("yaw",self._yawShare.get())
                self._serialDriver.send("state",self._state)

                if self._xShare.get() < 1400:
                    self._yShare.put(800)

                if self._serialDriver.read() == 'r':
                        self._state = S0

                if self._yawShare.get() < -(65 * pi/180): # after we have turned 65º, move to state 2
                    self._state = S2
                    self._waypointController.reset()
                    self._s2start = ticks_us()
                    

            elif self._state == S2:
                timeNow = ticks_us() - self._s2start

                if timeNow <= 2500000:
                    x = 1550 + (125 * math.cos(timeNow * pi / 5000000))
                    y = 600 - (125 * math.sin(timeNow * pi / 5000000))
                else:
                    x = 1550 - (timeNow - 2500000) / 20000
                    y = 475

                self._serialDriver.send("x_set",x)
                self._serialDriver.send("y_set",y)

                self._serialDriver.send("x",self._xShare.get())
                self._serialDriver.send("y",self._yShare.get())
                self._serialDriver.send("yaw",self._yawShare.get())
                self._serialDriver.send("state",self._state)

                if self._serialDriver.read() == 'r':
                        self._state = S0

                dist = math.sqrt((x - self._xShare.get())**2 + (y - self._yShare.get())**2)
                
                self._setpoint = dist
                if self._setpoint > 50:
                    self._setpoint = 50

                target_heading = math.atan2(y - self._yShare.get(), x - self._xShare.get())
                robot_heading = self._yawShare.get()
                yawError = math.atan2(math.sin(target_heading - robot_heading), math.cos(target_heading - robot_heading))

                yawAdjustment = self._waypointController.update(yawError)

                Rsetpoint = self._setpoint + yawAdjustment
                Lsetpoint = self._setpoint - yawAdjustment

                self._rightEncoder.update()
                Rvel = self._rightEncoder.get_velocity()
                Routput = self._rightController.update(Rsetpoint - Rvel)
                self._rightMotor.set_effort(Routput)

                self._leftEncoder.update()
                Lvel = self._leftEncoder.get_velocity()
                Loutput = self._leftController.update(Lsetpoint - Lvel)
                self._leftMotor.set_effort(Loutput)

                # if bump then stop
                if any(self._bumpDriver.read_bumps()):
                    self._state = S3
                    self._setpoint = 100
                    self._leftStartPos = self._leftEncoder.get_position()
                    self._rightStartPos = self._rightEncoder.get_position()

            elif self._state == S3:
                leftGood = False
                rightGood = False

                self._serialDriver.send("x",self._xShare.get())
                self._serialDriver.send("y",self._yShare.get())
                self._serialDriver.send("yaw",self._yawShare.get())
                self._serialDriver.send("state",self._state)

                if (self._leftEncoder.get_position() - self._leftStartPos) > -10:
                    self._leftMotor.set_effort(-10)
                else:
                    self._leftMotor.set_effort(0)
                    leftGood = True

                if (self._rightEncoder.get_position() - self._rightStartPos) > -10:
                    self._rightMotor.set_effort(-10)
                else:
                    self._rightMotor.set_effort(0)
                    rightGood = True
                
                if leftGood and rightGood:
                    self._state = S4

            elif self._state == S4:
                self._serialDriver.send("x",self._xShare.get())
                self._serialDriver.send("y",self._yShare.get())
                self._serialDriver.send("yaw",self._yawShare.get())
                self._serialDriver.send("state",self._state)

                if self._yawShare.get() < -(110*pi/180):
                    self._leftMotor.set_effort(-10)
                    self._rightMotor.set_effort(10)
                else:
                    self._rightController.reset()
                    self._leftController.reset()
                    self._lineController.reset()
                    self._state = S5

            elif self._state == S5:
                line_error = 0 - self._IR_driver.get_centroid()
                line_adjustment = self._lineController.update(line_error)

                Rsetpoint = self._setpoint + line_adjustment
                Lsetpoint = self._setpoint - line_adjustment

                self._rightEncoder.update()
                Rvel = self._rightEncoder.get_velocity()
                Routput = self._rightController.update(Rsetpoint - Rvel)
                self._rightMotor.set_effort(Routput)

                self._leftEncoder.update()
                Lvel = self._leftEncoder.get_velocity()
                Loutput = self._leftController.update(Lsetpoint - Lvel)
                self._leftMotor.set_effort(Loutput)

                self._serialDriver.send("x",self._xShare.get())
                self._serialDriver.send("y",self._yShare.get())
                self._serialDriver.send("yaw",self._yawShare.get())
                self._serialDriver.send("state",self._state)

                if self._yShare.get() < 125:
                    self._leftMotor.set_effort(0)
                    self._rightMotor.set_effort(0)
                    self._state = S6

            elif self._state == S6:
                self._serialDriver.send("x",self._xShare.get())
                self._serialDriver.send("y",self._yShare.get())
                self._serialDriver.send("yaw",self._yawShare.get())
                self._serialDriver.send("state",self._state)

                if self._yawShare.get() > -(170*pi/180):
                    self._leftMotor.set_effort(10)
                    self._rightMotor.set_effort(-10)
                else:
                    self._state = S7
                    self._leftMotor.set_effort(0)
                    self._rightMotor.set_effort(0)
                    self._lineController.set_kp(60) #30
                    self._lineController.set_ki(25) #20
                    self._rightController.reset()
                    self._leftController.reset()
                    self._lineController.reset()

            elif self._state == S7: # line following through obstacles
                self._serialDriver.send("x",self._xShare.get())
                self._serialDriver.send("y",self._yShare.get())
                self._serialDriver.send("yaw",self._yawShare.get())
                self._serialDriver.send("state",self._state)

                if self._xShare.get() < 300:
                    self._setpoint = 45
                else:
                    self._setpoint = 90

                line_error = 0 - self._IR_driver.get_centroid()
                line_adjustment = self._lineController.update(line_error)

                Rsetpoint = self._setpoint + line_adjustment
                Lsetpoint = self._setpoint - line_adjustment

                self._rightEncoder.update()
                Rvel = self._rightEncoder.get_velocity()
                Routput = self._rightController.update(Rsetpoint - Rvel)
                self._rightMotor.set_effort(Routput)

                self._leftEncoder.update()
                Lvel = self._leftEncoder.get_velocity()
                Loutput = self._leftController.update(Lsetpoint - Lvel)
                self._leftMotor.set_effort(Loutput)

                if self._yShare.get() > 425 and self._xShare.get() > 100:
                    self._rightController.reset()
                    self._leftController.reset()
                    self._waypointController.reset()
                    self._state = S8

            elif self._state == S8:
                self._serialDriver.send("x",self._xShare.get())
                self._serialDriver.send("y",self._yShare.get())
                self._serialDriver.send("yaw",self._yawShare.get())
                self._serialDriver.send("state",self._state)

                x = 400
                y = 475

                self._serialDriver.send("x_set",x)
                self._serialDriver.send("y_set",y)

                dist = math.sqrt((x - self._xShare.get())**2 + (y - self._yShare.get())**2)
                
                self._setpoint = dist * 2
                if self._setpoint > 80:
                    self._setpoint = 80

                target_heading = math.atan2(y - self._yShare.get(), x - self._xShare.get())
                robot_heading = self._yawShare.get()
                yawError = math.atan2(math.sin(target_heading - robot_heading), math.cos(target_heading - robot_heading))

                yawAdjustment = self._waypointController.update(yawError)

                Rsetpoint = self._setpoint + yawAdjustment
                Lsetpoint = self._setpoint - yawAdjustment

                self._rightEncoder.update()
                Rvel = self._rightEncoder.get_velocity()
                Routput = self._rightController.update(Rsetpoint - Rvel)
                self._rightMotor.set_effort(Routput)

                self._leftEncoder.update()
                Lvel = self._leftEncoder.get_velocity()
                Loutput = self._leftController.update(Lsetpoint - Lvel)
                self._leftMotor.set_effort(Loutput)

                # if bump then stop
                if dist < 25 or self._xShare.get() > 400:
                    self._serialDriver.send("x_set",-1000)
                    self._serialDriver.send("y_set",-1000)
                    self._state = S9

            elif self._state == S9:
                self._serialDriver.send("x",self._xShare.get())
                self._serialDriver.send("y",self._yShare.get())
                self._serialDriver.send("yaw",self._yawShare.get())
                self._serialDriver.send("state",self._state)

                if self._yawShare.get() < (-190 * pi/180):
                    self._rightMotor.set_effort(10)
                    self._leftMotor.set_effort(-10)
                else:
                    self._state = S10
                    self._waypointController.reset()
                    self._rightController.reset()
                    self._leftController.reset()
                    self._s10start = ticks_us()

            elif self._state == S10:
                self._serialDriver.send("x",self._xShare.get())
                self._serialDriver.send("y",self._yShare.get())
                self._serialDriver.send("yaw",self._yawShare.get())
                self._serialDriver.send("state",self._state)

                timeNow = ticks_us() - self._s10start

                if timeNow <= 2500000:
                    x = 300 - (200 * math.sin(timeNow * pi / 5000000))
                    y = 700 - (200 * math.cos(timeNow * pi / 5000000))
                else:
                    x = 100
                    y = 700 + (timeNow - 2500000) / 20000

                self._serialDriver.send("x_set",x)
                self._serialDriver.send("y_set",y)

                dist = math.sqrt((x - self._xShare.get())**2 + (y - self._yShare.get())**2)
                
                self._setpoint = dist * 2
                if self._setpoint > 80:
                    self._setpoint = 80

                target_heading = math.atan2(y - self._yShare.get(), x - self._xShare.get())
                robot_heading = self._yawShare.get()
                yawError = math.atan2(math.sin(target_heading - robot_heading), math.cos(target_heading - robot_heading))

                yawAdjustment = self._waypointController.update(yawError)

                Rsetpoint = self._setpoint + yawAdjustment
                Lsetpoint = self._setpoint - yawAdjustment

                self._rightEncoder.update()
                Rvel = self._rightEncoder.get_velocity()
                Routput = self._rightController.update(Rsetpoint - Rvel)
                self._rightMotor.set_effort(Routput)

                self._leftEncoder.update()
                Lvel = self._leftEncoder.get_velocity()
                Loutput = self._leftController.update(Lsetpoint - Lvel)
                self._leftMotor.set_effort(Loutput)

                # if bump then stop
                if self._yShare.get() > 800:
                    self._serialDriver.send("x_set",-1000)
                    self._serialDriver.send("y_set",-1000)
                    self._state = S11

            elif self._state == S11:
                self._serialDriver.send("x",self._xShare.get())
                self._serialDriver.send("y",self._yShare.get())
                self._serialDriver.send("yaw",self._yawShare.get())
                self._serialDriver.send("state",self._state)

                if self._yawShare.get() > (-2*pi):
                    self._rightMotor.set_effort(-10)
                    self._leftMotor.set_effort(10)
                else:
                    self._rightMotor.set_effort(0)
                    self._leftMotor.set_effort(0)
                    self._endTime = ticks_us()
                    self._state = S12

            elif self._state == S12:
                self._serialDriver.send("end_t",(self._endTime - self._startTime)/1000000)
                self._rightMotor.set_effort(0)
                self._leftMotor.set_effort(0)

                
            
            yield self._state