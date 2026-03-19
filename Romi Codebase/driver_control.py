from time import ticks_us, ticks_diff

class driver_control:
    '''A PID controller encapsulated in a Python class'''

    def __init__(self):
        '''Initializes an control object'''
        self.kp = 0
        self.ki = 0
        self.kd = 0

        self.err_int = 0
        self.err_dt = 0
        self.err_prev = 0

        self.dt         = 0     # Amount of time between last two updates
        self.ticks_prev = 0     # previous ticks number
    
    def reset(self):
        self.ticks_prev = ticks_us()
        self.err_int = 0
        self.err_prev = 0
        pass

    def update(self, err):
        self.dt = ticks_diff(ticks_us(), self.ticks_prev)
        self.ticks_prev = ticks_us()

        self.err_int += err * self.dt * 0.000001
        self.err_dt = (err - self.err_prev) / self.dt

        pid = (err * self.kp) + (self.err_int * self.ki) + (self.err_dt * self.kd)

        self.err_prev = err

        return pid

    def set_kp(self, kp):
        self.kp = kp
        pass

    def set_ki(self, ki):
        self.ki = ki
        pass

    def set_kd(self, kd):
        self.kd = kd
        pass