import zmq
import time
import gpiozero as gpz

# Connect to the camera server
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.setsockopt_string(zmq.SUBSCRIBE, "balloons")
socket.connect('tcp://127.0.0.1:5556')

def check_camera():
    # Read the balloon array
    try:
        message = socket.recv(flags = zmq.NOBLOCK)
        parts = message.decode('ascii').split(' ')
        data = [int(p) for p in parts[1:]]
        balloons = data[0:2], data[2:4], data[4:6]
    except zmq.error.Again:
        balloons = [(0,0), (0,0), (0,0)]
    return balloons

# set up GPIO hardware
PIEZOPIN = 4
BUTTONPIN = 25
LEDPIN = 22
buzzer = gpz.TonalBuzzer(PIEZOPIN)
led = gpz.LED(LEDPIN)
rmotor = gpz.Motor(20,16,12,pwm=True)
lmotor = gpz.Motor(26,19,5,pwm=True)
lsensor = gpz.DistanceSensor(24,21)
rsensor = gpz.DistanceSensor(27,13)
button = gpz.Button(BUTTONPIN, bounce_time=0.2)

def beep(length=0.01):
    buzzer.play("A4")
    time.sleep(length)
    buzzer.stop()
    
def read_sensors():
    return lsensor.distance, rsensor.distance

def move(throttle, steering=0):
    if steering > 0:
        rspeed = steering
        lspeed = 0
    else:
        lspeed = abs(steering)
        rspeed = 0
    rspeed = min(max(throttle+rspeed,0),1)
    lspeed = min(max(throttle+lspeed,0),1)
    rmotor.forward(rspeed)
    lmotor.forward(lspeed)
#     print(rspeed, lspeed)
    

time_sensors_checked = 0
distances = (None, None)

'''
State machine
PATROL: drive straight until encounters a wall or sees a balloon
TURNING: turn so that the wall is no longer detected.
REVERSING: reverse and turn around
FOUND_BALLOON: turn towards balloon and accelerate
STOPPED: button toggles between STOPPED and PATROL
'''
state = "stopped"
oldstate = None
print("Robot running")

def toggle_robot():
    if state == 'stopped':
        state == 'patrol'
    else:
        state == 'stopped'

button.when_pressed = toggle_robot

try:
    # check for balloon data
    balloons = check_camera()
    # check for obstacles
    if time.time() - time_sensors_checked > 0.05:
        distances = read_sensors()
        time_sensors_checked = time.time()
        found_obstacles = [d < 0.2 for d in distances]
    if state != oldstate:
        state_time = time.time()
        beep()
    state = oldstate
    time_in_state = time.time() - state_time
    print(state, time_in_state)
    
    if state == "stopped":
        move(0,0)
        led.on()    
    elif state == "patrol":
        move(100, 0)
        led.blink(0.25, 0.25)
        if any(found_obstacles):
            state = "turning"
    elif state == "turning":
        led.blink(0.5, 0.5)
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
#     time.sleep(0.05)
#     print(state, time.time())
        
finally:
    print('Stopping robot')
    move(0,0)
