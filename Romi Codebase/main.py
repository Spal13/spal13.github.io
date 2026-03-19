import machine

# drivers
from driver_motor   import driver_motor
from driver_encoder import driver_encoder
from driver_serial  import driver_serial

# tasks
from task_estimator import task_estimator
from task_navigator import task_navigator

# misc
from task_share     import Share, Queue, show_all
from cotask         import Task, task_list
from gc             import collect
from pyb            import Timer, Pin, ADC


# motor driver objects
MTR_PWM_tmr = Timer(1, freq=10000)
leftMotor    = driver_motor(Pin.cpu.A8, Pin.cpu.C7, Pin.cpu.A9, MTR_PWM_tmr, 1)
rightMotor   = driver_motor(Pin.cpu.A10, Pin.cpu.B5, Pin.cpu.B2, MTR_PWM_tmr, 3) # A10 B5 B3

# left encoder object
pinA1 = Pin(Pin.cpu.A15, mode=Pin.AF_PP) # A0
pinB1 = Pin(Pin.cpu.B3, mode=Pin.AF_PP) # A1
tim1 = Timer(2, prescaler=0, period=0xFFFF)
rightEncoder  = driver_encoder(tim1, pinA1, pinB1)

# right encoder object
pinA2 = Pin(Pin.cpu.A6, mode=Pin.AF_PP)
pinB2 = Pin(Pin.cpu.A7, mode=Pin.AF_PP)
tim2 = Timer(3, prescaler=0, period=0xFFFF)
leftEncoder = driver_encoder(tim2, pinA2, pinB2)

serialDriver = driver_serial()

# Shares and queues
xShare       = Share("f", name="x position (mm)")
yShare       = Share("f", name="y position (mm)")
yawShare     = Share("f", name="yaw (rad)")
homedShare   = Share("B", name ="homed status")
homedShare.put(False)

# Build task class objects
estimatorTask = task_estimator(leftEncoder, rightEncoder, xShare, yShare, yawShare, homedShare, serialDriver)
navigatorTask = task_navigator(leftEncoder, rightEncoder, leftMotor, rightMotor, xShare, yShare, yawShare, homedShare, serialDriver)

# Add tasks to task list
task_list.append(Task(estimatorTask.run, name="Estimator Task", priority = 2, period = 20, profile=False))
task_list.append(Task(navigatorTask.run, name="Navigator Task", priority = 1, period = 50, profile=False))

# Run the garbage collector preemptively
collect()

# Run the scheduler until the user quits the program with Ctrl-C
while True:
    try:
        task_list.pri_sched()
        
    except KeyboardInterrupt:
        print("Program Terminating")
        leftMotor.disable()
        rightMotor.disable()
        break

print("\n")
print(task_list)
print(show_all())