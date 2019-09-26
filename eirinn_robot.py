import RPi.GPIO as GPIO
import time
motors = [(20, 16, 12), #1,2, enable
              (26, 19, 5)] 
sensor_pins = [(21, 24), #trig, echo for left sensor
               (17, 13)] #trig, echo for right sensor
PIEZOPIN = 4
BUTTONPIN = 25
LEDPIN = 22
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

## Setup all pins and PWM objects
motor_pwm = []
for motorpins in motors:
    GPIO.setup(motorpins, GPIO.OUT)
    motor_pwm.append(GPIO.PWM(motorpins[2], 1000))
for sensorpins in sensor_pins:
    GPIO.setup(sensorpins[0], GPIO.OUT) #trig pin
    GPIO.setup(sensorpins[1], GPIO.IN) #echo pin
GPIO.setup(PIEZOPIN, GPIO.OUT)
GPIO.setup(LEDPIN, GPIO.OUT)
led_pwm = GPIO.PWM(LEDPIN, 2)
GPIO.setup(BUTTONPIN, GPIO.IN, GPIO.PUD_UP)

def beep(length=0.01):
    GPIO.output(PIEZOPIN, 1)
    time.sleep(length)
    GPIO.output(PIEZOPIN, 0)

def read_sensor(which_sensor=0):
    trig, echo = sensor_pins[which_sensor]
#     GPIO.setup(trig, GPIO.OUT, initial = 0)
#     GPIO.setup(echo, GPIO.IN)
    GPIO.output(trig, 1)
    time.sleep(0.00001) #10us pulse
    GPIO.output(trig, 0)
    time_pulse_sent = time.time()
    # wait till echo goes high
    while (GPIO.input(echo)==0):
        if time.time() - time_pulse_sent > 1:
            print("Timeout waiting for echo to go high")
            break
    start_time = time.time()
    while GPIO.input(echo)==1:
        pass
    pulse_length = time.time() - start_time
    return pulse_length * 170


def setspeed(motor, speed):
    # if speed is negative, flip direction
    p1, p2, en = motors[motor]
    direction = speed>0
    pwm_duty_cycle = abs(speed)
    GPIO.output(p1, direction)
    GPIO.output(p2, not direction)
    motor_pwm[motor].start(pwm_duty_cycle)

def move(throttle, steering=0):
    # simple formula. Make each wheel keep equal
    # differential speed from the main speed (throttle)
    # also max speed for each wheel is 100
    # first constrain steering to -100, 100
    steering = min(max(steering, -100), 100)
    # now calculate the max throttle for this
    if steering>0:
        max_throttle = 100-steering
    else:
        max_throttle = 100+steering
    throttle = min(max(throttle, -max_throttle), max_throttle)
    speed_left = throttle + steering
    speed_right = throttle - steering
    setspeed(0, speed_left)
    setspeed(1, speed_right)
    print(speed_left, speed_right)
'''
State machine
PATROL: drive straight until encounters a wall or sees a balloon
TURNING: turn so that the wall is no longer detected.
    if obstacles are detected on both sides, reverse and turn around
REVERSING: reverse and turn around
FOUND_BALLOON: turn towards balloon and accelerate
STOPPED: button toggles between STOPPED and PATROL
'''
state = "stopped"
print("Robot running")
while True:
    # check for obstacles
    found_obstacles = (read_sensor(0)<0.2, read_sensor(1)<0.2)
    # check button
    if state != "stopped" and (GPIO.input(BUTTONPIN)==0):
        state = "stopped"
        beep(1)
        
    if state == "stopped":
        move(0,0)
        led_pwm.stop()
        GPIO.output(LEDPIN, 1)
        if GPIO.input(BUTTONPIN)==0:
            print("button pressed")
            state = "patrol"
            for i in range(5):
                beep(0.1)
                time.sleep(0.2)
    elif state == "patrol":
        move(100, 0)
        led_pwm.start(50)
        led_pwm.ChangeFrequency(2)
        if any(found_obstacles):
            state = "turning"
    elif state == "turning":
        led_pwm.ChangeFrequency(1)
        if all(found_obstacles):
            state = "reversing"
        else:
            beep(0.05)
            if found_obstacles[0]: #turn to the right
                move(100, 50)
            elif found_obstacles[1]:
                move(100, -50)
            else:
                state = "patrol"
    elif state == "reversing":
        # reverse for 2 seconds
        for i in range(2):
            beep(0.5)
            move(-100, 0)
            time.sleep(0.5)
        move(0,-100)
        time.sleep(0.5)
        state = "patrol"
    time.sleep(0.05)
    print(state, time.time())



