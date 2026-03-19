# ME405 Final Project Report
This page will go over our groups hardware and software solution to complete the final obstacle course using our Romi Robot. 

The goal of this final project was to have the Romi complete an obstacle course. The obstacle course included line following, bump sensing, and location estimation challenges. To complete this task, our team relied on sensor data from hardware and algorithms implemented in software. This page will review our final design and implementation.  

## Hardware
The main hardware used was the Romi robot. The Romi robot is a differential drive robot with two DC motor powered wheels. It uses 70 mm diameter wheels and has a chassis diameter of about 165 mm. The Romi utilized a power distribution & motor driver combination PCB. The DC motors were integrated with quadrature encoders and operated via PWM. The Romi operated off of AA batteries in a 6S configuration (6 AA batteries in parallel), outputting approximately 8.4V nominally.   

### Sensors
- Communication Modules (ESP32)
- Custom Hardware (3D Prints)

Software
- Drivers
- Shares
- Tasks
- UI (Real Time Course Tracking)
