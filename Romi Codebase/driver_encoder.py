from pyb import Timer, Pin
from time import ticks_us, ticks_diff

class driver_encoder:
    '''A quadrature encoder decoding interface encapsulated in a Python class'''

    def __init__(self, tim, chA_pin, chB_pin):
        '''Initializes an Encoder object'''
        self.tim = tim
        self.tim.channel(1, Timer.ENC_AB, pin=chA_pin) # set pin A
        self.tim.channel(2, Timer.ENC_AB, pin=chB_pin) # set pin B

        self.count       = 0     # raw count
        self.count_prev  = 0     # raw count from previous cycle
        self.count_delta = 0     # raw count delta

        self.position    = 0     # nice accumulated position of the counter
        self.delta       = 0     # Change in count between last two updates

        self.dt         = 0     # Amount of time between last two updates
        self.ticks_prev = 0     # previous ticks number
        self.conversion = 153022.3543 # ticks/us to mm/s of wheel speed
    
    def update(self):
        '''Runs one update step on the encoder's timer counter to keep
           track of the change in count and check for counter reload'''

        self.count = self.tim.counter()
        self.count_delta = self.count - self.count_prev

        if(self.count_delta < -32768):
            self.delta = self.count_delta + 65536
        elif(self.count_delta > 32768):
            self.delta = self.count_delta - 65536
        else:
            self.delta = self.count_delta

        self.position += self.delta

        self.dt = ticks_diff(ticks_us(), self.ticks_prev)

        self.ticks_prev = ticks_us()
        self.count_prev = self.count
        pass

    def get_position(self):
        '''Returns the most recently updated value of position as determined
           within the update() method'''
        return self.position * 0.1530223543 # ticks to mm conversion
            
    def get_velocity(self):
        '''Returns a measure of velocity using the the most recently updated
           value of delta as determined within the update() method'''
        return (self.delta/self.dt) * self.conversion
    
    def zero(self):
        '''Sets the present encoder position to zero and causes future updates
           to measure with respect to the new zero position'''
        self.position = 0
        pass