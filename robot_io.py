import gpiozero as io
import time

# buzzer = io.TonalBuzzer()
rmotor = io.Motor(20,16,12,pwm=True)
lmotor = io.Motor(26,19,5,pwm=True)
lsensor = io.DistanceSensor(24,21)
rsensor = io.DistanceSensor(27,13)
# button = io.Button()

def beep(length=0.01):
    buzzer.play("A4")
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
    




