# ME405 Final Project Report
This page will go over our groups hardware and software solution to complete the final obstacle course using our Romi Robot. 

The goal of this final project was to have the Romi complete an obstacle course. The obstacle course included line following, bump sensing, and location estimation challenges. To complete this task, our team relied on sensor data from hardware and algorithms implemented in software. This page will review our final design and implementation.  

## Hardware
### Romi
The main hardware used was the Romi robot. The Romi robot is a differential drive robot with two DC motor powered wheels. It uses 70 mm diameter wheels and has a chassis diameter of about 165 mm. The Romi utilized a power distribution & motor driver combination PCB. The DC motors were integrated with quadrature encoders and operated via PWM. The Romi operated off of AA batteries in a 6S configuration (6 AA batteries in parallel), outputting approximately 8.4V nominally. 

### Sensors
#### Encoders
The Romi uses quadrature incremental encoders attached to the motors to measure wheel rotation. These encoders generate two digital signals that are offset in phase, allowing both the amount of rotation and the direction of motion to be determined. In this project, the STM32 timer hardware was used in encoder mode to read the pulses efficiently. The encoder counts were then used to track wheel position, and the change in counts over time was used to calculate wheel velocity.
#### Line Sensor
The line sensor used was a QTRX-MD-13A analog reflectance sensor array with 13 sensors spaced at 8 mm pitch, though only 9 sensors were used in this project. The board was powered from a 3.3V supply from the STM32 NUCLEO board. Each sensor on this array output analog voltages based on surface reflectivity. These analog readings were calibrated and used to generate a centroid value, which provided an estimate of the line position for line following.
#### IMU
The system uses a BNO055 inertial measurement unit, which integrates a 3-axis accelerometer, gyroscope, and magnetometer. The sensor operates over I2C and performs onboard sensor fusion to provide orientation data directly as Euler angles (roll, pitch, and yaw). The IMU also provides angular velocity measurements from the gyroscope. The main data captured from the IMU was the YAW of the Romi for navigation control without using the line sensor. 
#### Bump Sensors
The system uses snap-action SPDT mechanical switches as bump sensors to detect collisions with obstacles. Each switch is connected with an external pull up resistor that we integrated into the cable/harness of each bump sensor, creating an active low digital input to the microcontroller. Two sensors (left and right) were placed in the front of Romi and was used to detect which side of the robot encountered an obstacle. When the switch is pressed, the input is pulled low, indicating the Romi has bumped into an obstacle. 

### Control System
#### STM32 w/ Shoe of Brian
### Communication System
#### Communication Module (ESP32)

### Custom 3D Prints
In addition to the Romi, sensors were added to generate more data about its surroundings, orientation in addition to the movement data generated my the encoders. 
- Communication Modules (ESP32)
- Custom Hardware (3D Prints)

## Software
- Language
- Drivers
- Shares
- Tasks
- UI (Real Time Course Tracking)

