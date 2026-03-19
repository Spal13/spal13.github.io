from driver_encoder import driver_encoder
from driver_IMU     import driver_IMU
from task_share     import Share, Queue
from utime          import ticks_us, ticks_diff
from time import sleep_ms
import micropython
from pyb import I2C
from ulab import numpy as np
import math

# TODO
# change static update time (20ms) in integration to use real dt

S0_INIT = micropython.const(0)  # State 0 - initialiation
S1_HOME = micropython.const(1) # State 1 - set home position and hading
S2_RUN  = micropython.const(2)  # State 2 - run

class task_estimator:

    def __init__(self, leftEncoder, rightEncoder, xShare, yShare, yawShare, homedShare, serialDriver):

        self._state: int = S0_INIT    # The present state of the task

        self._leftEncoder = leftEncoder
        self._rightEncoder = rightEncoder
        self._xShare = xShare
        self._yShare = yShare
        self._yawShare = yawShare
        self._homedShare = homedShare

        self._yawSum = 0.0
        self._calibCounts = 0 # current number of calibration counts
        self._calibCountsMax = 50 # how many times to run the zero-angle calibration state

        self._yawEnc = 0.0 # yaw based only on encoder
        self._yawImu = 0.0 # yaw based only on IMU heading value

        self._i2c = I2C(2, I2C.CONTROLLER, baudrate=400000)
        self._imu = driver_IMU(self._i2c, "PC10")
        self._imu.operMode("NDOF")

        self._zeroYaw = 0.0 # zero angle from IMU heading
        self._lastYaw = 0.0 # last angle from IMU heading
        self._rotations: int = 0 # how many rotations romi has made
        self._ran = False

        self._Xenc = 0.0 # x positon based only on encoder data
        self._Yenc = 0.0 # y positon based only on encoder data
        
        self._Ximu = 0.0 # x positon based on encoder lengths and IMU heading
        self._Yimu = 0.0 # y positon based on encoder lengths and IMU heading

        
    def run(self):
        '''
        Runs one iteration of the task
        '''
        
        while True:
            
            if self._state == S0_INIT: # Init state

                #connect to the IMU and use stored calibration data
                try:
                    f = open("imu_calib.txt")
                    
                    print("Calibration file found.")
                    coeff = bytearray(22)
                    for i in range(22):
                        coeff[i] = int(f.readline())
                    f.close()
                    self._imu.calibSet(coeff)
                    sleep_ms(100)
                    print("Calibration loaded")

                except OSError:
                    print("No calibration file found")

                self._yawSum = 0.0
                self._state = S1_HOME

            elif self._state == S1_HOME:

                if self._calibCounts < self._calibCountsMax:
                    self._yawSum += self._imu.getAngle("YAW")
                    self._calibCounts += 1
                    print("Homing...")
                else:
                    self._zeroYaw = self._yawSum / self._calibCountsMax # get average heading
                    self._yawSum = 0.0 # clear yaw sum
                    self._yawEnc = 0.0
                    self._rotations = 0
                    self._yawImu = 0.0

                    self._Xenc = 100
                    self._Yenc = 800
                    self._Ximu = 100
                    self._Yimu = 800

                    self._homedShare.put(True) # say that we are good to go
                    self._lastYaw = self._imu.getAngle("YAW") # update last yaw
                    print("Homed!")
                    self._state = S2_RUN # go to run


            elif self._state == S2_RUN:
                
                # update yaw based only on encoders
                self._leftEncoder.update()
                self._rightEncoder.update()
                self._yawEnc = (1/140) * (self._rightEncoder.get_position() - self._leftEncoder.get_position())

                # update x & y based only on encoders
                leftEncoderVelocity = self._leftEncoder.get_velocity()
                rightEncoderVelocity = self._rightEncoder.get_velocity()
                #self._Xenc += math.cos(self._yawEnc) * (leftEncoderVelocity + rightEncoderVelocity)/2 * 0.02
                #self._Yenc += math.sin(self._yawEnc) * (leftEncoderVelocity + rightEncoderVelocity)/2 * 0.02

                self._Xenc = self._xShare.get() + math.cos(self._yawEnc) * (leftEncoderVelocity + rightEncoderVelocity)/2 * 0.02
                self._Yenc = self._yShare.get() + math.sin(self._yawEnc) * (leftEncoderVelocity + rightEncoderVelocity)/2 * 0.02

                # update yaw based only on IMU
                rawYaw = self._imu.getAngle("YAW") # 0 to 2pi

                if self._lastYaw > ((3/2) * np.pi) and rawYaw < np.pi/2: # if last yaw is between 3/2 pi & 4/2pi and now we are between 0 pi & 1/2 pi, then we went up by 2pi
                    self._rotations += 1

                if self._lastYaw < np.pi/2 and rawYaw > ((3/2) * np.pi): # if last yaw is between 0 pi & 1/2 pi, and now we are between 3/2 pi & 4/2 pi, then we went down by 2 pi
                    self._rotations -= 1

                self._lastYaw = rawYaw

                self._yawImu = (self._imu.getAngle("YAW") - self._zeroYaw + (self._rotations * 2 * np.pi)) * -1

                # update x & y based on IMU and encoders
                self._Ximu += math.cos(self._yawImu) * (leftEncoderVelocity + rightEncoderVelocity)/2 * 0.02
                self._Yimu += math.sin(self._yawImu) * (leftEncoderVelocity + rightEncoderVelocity)/2 * 0.02

                # update shares
                self._xShare.put(self._Xenc)
                self._yShare.put(self._Yenc)
                self._yawShare.put(self._yawEnc)

                if self._homedShare.get() == False: # if we are not homed, then do that
                    self._state = S1_HOME

            
            yield self._state