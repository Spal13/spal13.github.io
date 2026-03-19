from pyb import Pin, I2C
import time

class driver_IMU:
    '''IMU BNO055 sensor driver encapsulated in a Python class
    interface via I2C'''

    def __init__(self, i2c, RST_pin):
        '''Initializes an IMU sensor object'''

        # Device I2C Address
        self.imu_addr = 0x28                # Default BNO055 I2C address (ADR pin LOW)

        # Key Control / Status Registers
        self.OPER_MODE_reg = 0x3D           # Operation Mode register: selects fusion mode
        self.CAL_STAT_reg  = 0x35           # Calibration status register: 2-bit fields for SYS, GYR, ACC, MAG calibration level
        self.CAL_COEF_offset = 0x55         # Start address of 22-byte calibration data block (0x55–0x6A)

        # Euler Angle Output Registers (LSB addresses)
        self.EUL_YAW_offset   = 0x1A        # Heading/Yaw LSB register (0x1A LSB, 0x1B MSB)
        self.EUL_ROLL_offset  = 0x1C        # Roll LSB register    (0x1C LSB, 0x1D MSB)
        self.EUL_PITCH_offset = 0x1E        # Pitch LSB register   (0x1E LSB, 0x1F MSB)

        # Angular Velocity (Gyro) Output Registers (LSB addresses)
        self.ROLL_RATE_offset  = 0x14       # Gyro X-axis rate LSB (0x14 LSB, 0x15 MSB)
        self.PITCH_RATE_offset = 0x16       # Gyro Y-axis rate LSB (0x16 LSB, 0x17 MSB)
        self.YAW_RATE_offset   = 0x18       # Gyro Z-axis rate LSB (0x18 LSB, 0x19 MSB)

        # Operation Mode Values (write these into OPER_MODE_reg = 0x3D)
        self.CONFIG_MODE        = 0b0000    # CONFIG mode: required for calibration read/write and certain configuration changes
        self.IMU_MODE           = 0b1000    # IMU fusion: accel + gyro (no magnetometer)
        self.COMPASS_MODE       = 0b1001    # Compass fusion: accel + magnetometer (no gyro)
        self.M4G_MODE           = 0b1010    # M4G fusion: accel + magnetometer orientation estimate (no gyro)
        self.NDOF_FMC_OFF_MODE  = 0b1011    # NDOF fusion with Fast Magnetometer Calibration disabled
        self.NDOF_MODE          = 0b1100    # Full 9-DOF fusion: accel + gyro + magnetometer

        # Offset values ot "home" IMU
        self.ROLL_offset  = 0
        self.PITCH_offset = 0
        self.YAW_offset   = 0

        # Initialize the RST pin
        self.RST = Pin(RST_pin,  mode=Pin.OUT_PP)
        
        # Initialize I2C bus
        self.i2c = i2c
        print("IMU_driver: stored i2c")

        # Reset the IMU to place in CONFIG mode
        print("IMU_driver: toggling RST")
        self.RST.high()
        time.sleep_ms(1)
        self.RST.low()
        time.sleep_ms(10)
        self.RST.high()
        time.sleep_ms(650)
        print("IMU_driver: reset complete")

    def operMode(self, MODE):
        '''
        Sets the operating mode of the BNO055 by writing to the Operation Mode register (0x3D).

        Available fusion modes:
        "IMU"            - Uses accelerometer and gyroscope to compute relative orientation.
        "COMPASS"        - Uses accelerometer and magnetometer to compute geographic heading.
        "M4G"            - Uses accelerometer and magnetometer (no gyroscope) to estimate orientation.
        "NDOF_FMC_OFF"   - Full 9-DOF fusion with Fast Magnetometer Calibration disabled.
        "NDOF"           - Full 9-DOF fusion using accelerometer, gyroscope, and magnetometer.

        After writing the mode, a 19 ms delay is required per the datasheet to allow
        transition from CONFIG mode to the selected fusion mode.
        '''

        mode_sw_time = 19  # ms
        
        if MODE == "IMU":
            self.i2c.mem_write(self.IMU_MODE, self.imu_addr, self.OPER_MODE_reg, timeout=5, addr_size=8)
            time.sleep_ms(mode_sw_time)
        elif MODE == "COMPASS": 
            self.i2c.mem_write(self.COMPASS_MODE, self.imu_addr, self.OPER_MODE_reg, timeout=5, addr_size=8)
            time.sleep_ms(mode_sw_time)
        elif MODE == "M4G": 
            self.i2c.mem_write(self.M4G_MODE, self.imu_addr, self.OPER_MODE_reg, timeout=5, addr_size=8)
            time.sleep_ms(mode_sw_time)
        elif MODE == "NDOF_FMC_OFF": 
            self.i2c.mem_write(self.NDOF_FMC_OFF_MODE, self.imu_addr, self.OPER_MODE_reg, timeout=5, addr_size=8)
            time.sleep_ms(mode_sw_time)
        elif MODE == "NDOF": 
            self.i2c.mem_write(self.NDOF_MODE, self.imu_addr, self.OPER_MODE_reg, timeout=5, addr_size=8)
            time.sleep_ms(mode_sw_time)
        else:
            raise ValueError("Invalid MODE selection: Expect IMU, COMPASS, M4G, NDOF_FMC_OFF, or NDOF")
        
        print(f"IMU_driver: MODE set to {MODE}")
        

    def calibStat(self):
        '''Returns the parsed calibration status byte from the IMU'''

        status = self.i2c.mem_read(1, self.imu_addr, self.CAL_STAT_reg, timeout=5, addr_size=8)[0]

        SYS = (status >> 6) & 0b11
        GYR = (status >> 4) & 0b11
        ACC = (status >> 2) & 0b11
        MAG = status & 0b11

        return (SYS, GYR, ACC, MAG)

    def calibRead(self):
        '''Returns the calibration coefficients from the IMU as binary data.'''

        # Store current mode 
        current_mode = self.i2c.mem_read(1, self.imu_addr, self.OPER_MODE_reg, timeout=5, addr_size=8)[0]
        current_mode = current_mode & 0x0F

        mode_sw_time = 19 # Time for IMU to switch from any mode to CONFIG mode

        # Switch to CONFIG mode
        self.i2c.mem_write(self.CONFIG_MODE, self.imu_addr, self.OPER_MODE_reg, timeout=5, addr_size=8)
        time.sleep_ms(mode_sw_time)

        coeff = bytearray(22)
        self.i2c.mem_read(coeff, self.imu_addr, self.CAL_COEF_offset, timeout=5, addr_size=8)

        mode_sw_time = 7 # Time for IMU to switch from CONFIG mode to any other mode

        # Switch to previous mode
        self.i2c.mem_write(current_mode, self.imu_addr, self.OPER_MODE_reg, timeout=5, addr_size=8)
        time.sleep_ms(mode_sw_time)

        return(coeff)


    def calibSet(self, coeff):
        '''Writes calibration coefficients back to the IMU from pre-recorded binary data'''

        if len(coeff) != 22:
            raise ValueError("Invalid size of calibration coefficients: Expect 22 bytes")

        # Store current mode 
        current_mode = self.i2c.mem_read(1, self.imu_addr, self.OPER_MODE_reg, timeout=5, addr_size=8)[0]
        current_mode = current_mode & 0x0F

        mode_sw_time = 19 # Time for IMU to switch from any mode to CONFIG mode

        # Switch to CONFIG mode
        self.i2c.mem_write(self.CONFIG_MODE, self.imu_addr, self.OPER_MODE_reg, timeout=5, addr_size=8)
        time.sleep_ms(mode_sw_time)

        # Write coeff to calibration registers 
        self.i2c.mem_write(coeff, self.imu_addr, self.CAL_COEF_offset, timeout=5, addr_size=8)

        mode_sw_time = 7 # Time for IMU to switch from CONFIG mode to any other mode

        # Switch to previous mode
        self.i2c.mem_write(current_mode, self.imu_addr, self.OPER_MODE_reg, timeout=5, addr_size=8)
        time.sleep_ms(mode_sw_time)


    def getAngle(self, angle_type):
        '''Returns individual Euler angle in deg: roll, pitch, or yaw'''

        # Create a byte array buffer for two bytes
        angle_bytes = bytearray(2)

        if angle_type == "YAW":
            self.i2c.mem_read(angle_bytes, self.imu_addr, self.EUL_YAW_offset, timeout=5, addr_size=8)
        
        elif angle_type == "PITCH": 
            self.i2c.mem_read(angle_bytes, self.imu_addr, self.EUL_PITCH_offset, timeout=5, addr_size=8)
        
        elif angle_type == "ROLL": 
            self.i2c.mem_read(angle_bytes, self.imu_addr, self.EUL_ROLL_offset, timeout=5, addr_size=8)
        else:
            raise ValueError("Invalid angle selection: Expect ROLL, PITCH, or YAW")
        
        # Combine two 8 bit bytes data into one 16 bit word
        angle_word = (angle_bytes[1] << 8) | angle_bytes[0]

        # Convert signed 16-bit value
        if angle_word > 32767:
            angle_word -= 65536

        # Convert to radians
        angle = float(angle_word / 16 * 3.141592654 / 180) # negative 1 to match romi frame

        return angle

    def getAngleRate(self, rate_type):
        '''Returns individual angular velocity in deg/s: yaw rate, pitch rate, roll rate'''

        # Create a byte array buffer for two bytes
        rate_bytes = bytearray(2)

        if rate_type == "YAW":
            self.i2c.mem_read(rate_bytes, self.imu_addr, self.YAW_RATE_offset, timeout=5, addr_size=8)
        
        elif rate_type == "PITCH": 
            self.i2c.mem_read(rate_bytes, self.imu_addr, self.PITCH_RATE_offset, timeout=5, addr_size=8)
        
        elif rate_type == "ROLL": 
            self.i2c.mem_read(rate_bytes, self.imu_addr, self.ROLL_RATE_offset, timeout=5, addr_size=8)
        else:
            raise ValueError("Invalid angle rate selection: Expect ROLL, PITCH, or YAW")
        
        # Combine two 8 bit bytes data into one 16 bit word
        rate_word = (rate_bytes[1] << 8) | rate_bytes[0]

        # Convert signed 16-bit value
        if rate_word > 32767:
            rate_word -= 65536

        # Convert to degrees
        rate = float(rate_word / 16 * 3.141592654 / 180)
        return rate
    
    # def home(self):
    #     '''Capture the current orientation as the zero reference'''

    #     # Offset values ot "home" IMU
    #     self.ROLL_offset  = 0
    #     self.PITCH_offset = 0
    #     self.YAW_offset   = 0

    #     self.YAW_offset   = self.getAngle("YAW")
    #     self.PITCH_offset = self.getAngle("PITCH")
    #     self.ROLL_offset  = self.getAngle("ROLL")
    
