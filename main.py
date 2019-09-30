import zmq
import time
import datetime
import gpiozero as gpz
import random

# Connect to the camera server
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.setsockopt_string(zmq.SUBSCRIBE, "balloons")
socket.connect('tcp://127.0.0.1:5556')


def check_camera():
    # Read the balloon array
    try:
        message = socket.recv(flags=zmq.NOBLOCK)
        parts = message.decode('ascii').split(' ')
        data = [int(p) for p in parts[1:]]
        balloons = data[0:2], data[2:4], data[4:6]
        balloons = [(p, h) if h else None for p, h in balloons]
    except zmq.error.Again:
        balloons = None
    return balloons


# set up GPIO hardware
PIEZOPIN = 4
BUTTONPIN = 25
LEDPIN = 22
LED_RED_PIN = 23
buzzer = gpz.TonalBuzzer(PIEZOPIN)
led = gpz.LED(LEDPIN)
led_red = gpz.LED(LED_RED_PIN)
rmotor = gpz.Motor(20, 16, 12, pwm=True)
lmotor = gpz.Motor(26, 19, 5, pwm=True)
lsensor = gpz.DistanceSensor(21, 24)  # echo, trigger
rsensor = gpz.DistanceSensor(13, 27)
lsensor._queue.stop()  # stop the auto-checking
rsensor._queue.stop()  # stop the auto-checking
button = gpz.Button(BUTTONPIN, bounce_time=0.2)


def beep(length=0.1, freq=500):
    buzzer.play(freq)
    time.sleep(length)
    buzzer.stop()


def read_sensors():
    # lsensor._read()
    # rsensor._read()
    return lsensor._read(), rsensor._read()


def setspeed(motor, speed):
    if speed >= 0:
        motor.forward(speed/100)
    else:
        motor.backward(-speed/100)


def move(throttle, steering=0):
    # simple formula. Make each wheel keep equal
    # differential speed from the main speed (throttle)
    # also max speed for each wheel is 100
    # first constrain steering to -100, 100
    steering = min(max(steering, -100), 100)
    # now calculate the max throttle for this
    if steering > 0:
        max_throttle = 100-steering
    else:
        max_throttle = 100+steering
    throttle = min(max(throttle, -max_throttle), max_throttle)
    speed_left = throttle + steering
    speed_right = throttle - steering
    setspeed(lmotor, speed_left)
    setspeed(rmotor, speed_right)


time_sensors_checked = 0
distances = (None, None)

'''
State machine
PATROL: drive straight until encounters a wall or sees a balloon
TURNING: turn so that the wall is no longer detected.
REVERSING: reverse and turn around
SCANNING: turn on the spot
FOUND_BALLOON: turn and move towards balloon
STOPPED: button toggles between STOPPED and PATROL
'''
state = "stopped"
oldstate = None
print("Robot running")


def toggle_robot():
    global state
    if state == 'stopped':
        state = 'patrol'
    else:
        state = 'stopped'


green_balloons_remaining = 1


def balloon_found():
    global green_balloons_remaining
    if balloons:  # only proceed if there's valid data from the camera
        red, green, blue = balloons
        if green:
            if green_balloons_remaining == 0:
                green_balloons_remaining = 1
            return True
        elif red and green_balloons_remaining == 0:
            return True


time_button_pressed = 0
popping_range = False

try:
    while True:
        if button.is_pressed:
            if time.time() - time_button_pressed > 0.5:
                toggle_robot()
                time_button_pressed = time.time()

        if state != oldstate:
            state_time = time.time()
            # beep()
            print(state)
        oldstate = state
        time_in_state = time.time() - state_time

        ########### Check sensors ############
        # check for balloon data
        balloons = check_camera()
        # can we see a balloon that we want to target?
        # check for obstacles
        if time.time() - time_sensors_checked > 0.05:
            distances = read_sensors()
            time_sensors_checked = time.time()
            found_obstacles = [d < 0.2 if d else False for d in distances]



        ########### Run state machine ############
        if state == "stopped":
            move(0, 0)
            led.on()
        elif state == "patrol":
            # drive forwards for 2 seconds
            move(100, 0)
            led.blink(0.25, 0.25)
            if balloon_found():
                state = "found_balloon"
            elif time_in_state > 3:
                state = "scanning"
            elif any(found_obstacles):
                state = "turning"
        elif state == "turning":
            # turn to avoid obstacle
            led.blink(0.5, 0.5)
            if all(found_obstacles) and time_in_state > 0.5:
                state = "reversing"
            else:
                # beep(0.05)
                if found_obstacles[0]:  # turn to the right
                    # print("turning right")
                    move(0, -100)
                elif found_obstacles[1]:
                    move(0, 100)
                    # print("turning left")
                elif time_in_state > 0.3:
                    # time.sleep(0.3)
                    state = "patrol"
        elif state == "reversing":
            # reverse for 2 seconds then turn around
            move(-100, 0)
            time.sleep(0.25)
            move(0, -100)
            time.sleep(0.25)
            state = "patrol"
        elif state == "scanning":
            # Turn on the spot, looking for balloons. But which direction?
            direction = datetime.datetime.now().second % 4 >= 2
            if direction:
                move(0, 100)
            else:
                move(0, -100)
            if balloon_found():
                state = "found_balloon"
            elif time_in_state > 0.75:
                # give up, go back to patrolling
                state = "patrol"
        elif state == "found_balloon":
            beep(0.01)
            # do we have valid balloon data?
            if balloons:
                if balloon_found():
                    led_red.on()
                    # turn to face the balloon
                    red, green, blue = balloons
                    target = green if green else red
                    move(100, -target[0])

                    # see if balloon is in range of popping!
                    popping_range = target[1] > 240
                else:
                    # balloon disappeared...
                    if popping_range:
                        print("Balloon popped!")
                        green_balloons_remaining = max(
                            0, green_balloons_remaining - 1)
                        led_red.blink(0.3, 0.3)
                        beep(0.5)
                    #  but don't respond right away
                    if time_in_state > 0.3:
                        state = "patrol"
                        led_red.off()
            else:
                # camera failure... ignore it
                pass


finally:
    print('Stopping robot')
    led.off()
    led_red.off()
    beep()
    move(0, 0)
