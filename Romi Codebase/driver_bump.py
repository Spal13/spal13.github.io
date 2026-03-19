from pyb import Pin
import time

class driver_bump:
    '''Bump sensor driver for left and right bump sensors'''

    def __init__(self, left_pin, right_pin):
        '''Initialize left and right bump sensor pins'''
        self.left = Pin(left_pin, Pin.IN)
        self.right = Pin(right_pin, Pin.IN)

    def read_bumps(self):
        '''Return debounced bump states as [left, right]'''
        left_count = 0
        right_count = 0

        for i in range(5):   # debounce with 10 readings
            if self.left.value():
                left_count += 1
            if self.right.value():
                right_count += 1
            time.sleep_ms(1)

        if left_count >= 5:
            left_pressed = False
        else:
            left_pressed = True

        if right_count >= 5:
            right_pressed = False
        else:
            right_pressed = True

        return (left_pressed, right_pressed)