from pyb import Timer, Pin, ADC

class driver_IR:
    '''IR sensor driver encapsulated in a Python class'''

    def __init__(self, pins, serialDriver):
        '''Initializes an IR sensor object'''
        self.adc = []
        for pin in pins:
            self.adc.append(ADC(Pin(pin)))

        self._serialDriver = serialDriver

        self.whitePoint = [500] * len(self.adc) # Set up calibration array for white point of each sensor
        self.blackPoint = [3000] * len(self.adc) # Set up calibration array for black point of each sensor
        self._confidence = 0.0 # confidence from 0 to 100

    def calibrateWhite(self):
        '''Calibrate each sensor over white surface'''
        totals = [0] * len(self.adc)

        for j in range(100):   # take 100 samples
            for i in range(len(self.adc)):
                totals[i] += self.adc[i].read()

        for i in range(len(self.adc)): # Get average for each sensor
            self.whitePoint[i] = totals[i] / 100

        return self.whitePoint

    def calibrateBlack(self):
        '''Calibrate each sensor over black surface'''
        totals = [0] * len(self.adc)

        for j in range(100):   # take 100 samples
            for i in range(len(self.adc)):
                totals[i] += self.adc[i].read()

        for i in range(len(self.adc)): # Get average for each sensor
            self.blackPoint[i] = totals[i] / 100

        return self.blackPoint
    
    def calibSet(self, calibWhite, calibBlack):
        '''Write to both the blackPoint & whitePoint calibration arrays'''
        if (len(calibWhite) != len(self.adc)) or (len(calibBlack) != len(self.adc)):
            raise ValueError("Calibration values need to match the number of IR sensors")

        self.whitePoint = calibWhite
        self.blackPoint = calibBlack

    def get_centroid(self):
        '''Returns a value from 0 (white) to 100 (black)'''
        running_sum = 0
        position = -4
        area = 0

        for i in range(len(self.adc)):
            val = (self.adc[i].read() - self.whitePoint[i]) * 100 / (self.blackPoint[i] - self.whitePoint[i])

            if val > 100:
                val = 100
            elif val < 0:
                val = 0

            self._serialDriver.send("ir" + str(i), val)

            running_sum += position * val
            area += val
            position += 1

            #print(f"{val:03.0f}",end=',') # re-enable for Processing visualization

        if(area != 0):
            centroid = running_sum/area
        else:
            centroid = 0
        
        #print(centroid) # re-enable for Processing visualization
        return centroid

    def get_confidence(self):
        return self._confidence
    
    def get_std_dev(self):
        '''Returns the standard deviation of the normalized IR values'''

        values = []

        # get normalized values
        for i in range(len(self.adc)):

            val = (self.adc[i].read() - self.whitePoint[i]) * 100 / (self.blackPoint[i] - self.whitePoint[i])

            if val > 100:
                val = 100
            elif val < 0:
                val = 0

            values.append(val)

        # calculate mean
        total = 0
        for v in values:
            total += v

        mean = total / len(values)

        # calculate sum of squared differences
        total_sq_diff = 0
        for v in values:
            diff = v - mean
            total_sq_diff += diff * diff

        # calculate standard deviation
        std_dev = (total_sq_diff / len(values)) ** 0.5

        return std_dev