from pyb import Pin, ADC

class driver_battery:
    '''Battery driver for the Romi battery voltage. Returns SOC & Gain mutliplier for motors'''

    def __init__(self, adc_pin):
        '''Initialize the battery voltage input adc pin'''
        batt_pin = Pin(adc_pin)
        self.batt_adc = ADC(batt_pin)

        self.full_charge = (1.4 * 6)
        self.no_charge = (1 * 6)
        self.battery_dV = (self.full_charge - self.no_charge)

    def voltage(self):
        adc = self.batt_adc.read()
        v_adc = (adc / 4095 * 3.3) * 1.202
        v_batt = v_adc * 2.72
        return v_batt

    def SOC(self):
        '''Returns the battery SOC percentage'''

        batt_voltage = 0

        for i in range(10):
            v = self.voltage()
            batt_voltage += v

        batt_voltage = batt_voltage / 10

        SOC = 100 * ((batt_voltage - self.no_charge) / self.battery_dV)

        if SOC > 100:
            SOC = 100
        elif SOC < 0:
            SOC = 0

        return SOC

    def gain(self):
        '''Returns the gain multiplier based on current battery voltage'''

        batt_voltage = 0

        for i in range(10):
            v = self.voltage()
            batt_voltage += v

        batt_voltage = batt_voltage / 10

        gain = self.full_charge / batt_voltage

        return gain
        




