import RPi.GPIO as GPIO
import gpiozero as io
import time
motors = [(20, 16, 12), #1,2, enable
              (26, 19, 5)] 
sensor_pins = [(21, 6), #trig, echo for left sensor
               (18, 13)] #trig, echo for right sensor
PIEZOPIN = 4
BUTTONPIN = 25
LEDPIN = 22

rmotor = io.Motor(20,16,pwm=True)
lmotor = io.Motor(26,19,pwm=True)
