from pyb import Timer, Pin
import time

class driver_motor:
    '''This is a motor driver interface writen as a Python class. 
    This driver is intended to work with the Pololu DRV8838 Single Brushed DC Motor Driver found on the Romi Motor Driver and Power Distribution Board'''

    def __init__(self, PWM_pin: Pin, 
                 
                 DIR_pin: Pin, 

                 nSLP_pin: Pin,

                 tmr: Timer,

                 chan: int): 
        '''Initializes the pins and timer of the motor object. Inputs: PWM, DIR, nSLP are of the PIN type. Input TIM is of the Timer type. Input TIMch is of the int type''' 

        # Store a copy of each input parameter as an attribute 
        self.DIR_pin  = Pin(DIR_pin,  mode=Pin.OUT_PP) 

        self.nSLP_pin = Pin(nSLP_pin, mode=Pin.OUT_PP) 

        self.PWM_chan = tmr.channel(chan, 

                                    pin=PWM_pin, 

                                    mode=Timer.PWM, 

                                    pulse_width_percent=0)  

        self._effort: int = 0

        self._batVoltage: float = 8.4

    def set_effort(self, effort: float):
        '''This sets the direction and PWM pulse width percent based on the input value'''

        # Sets the direction to FWD if effort is greater that 0
        if effort > 0: 
            self._effort = effort
            self.DIR_pin.low()

            # Ensures that the maximum pulse width percent is 100
            if effort > 100:
                effort = 100

            self.PWM_chan.pulse_width_percent(effort)

        # Sets the direction to REV because effort is < 0
        else:
            self._effort = effort
            self.DIR_pin.high()
            effort = abs(effort)

            # Ensures that the maximum pulse width percent is 100
            if effort > 100:
                effort = 100

            self.PWM_chan.pulse_width_percent(effort)

    def get_voltage(self):
        return self._effort * 0.01 * self._batVoltage

    def enable(self):
        '''Enables the motor driver by taking it out of sleep mode (coast mode) into brake mode'''

        # This takes the motors out of sleep (out of coast mode) and into break mode
        self.nSLP_pin.high()
        self.PWM_chan.pulse_width_percent(0)

    def disable(self):
        '''Disables the motor driver by taking it into sleep mode (coast mode)'''

        self.nSLP_pin.low()




