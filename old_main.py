from imutils.video import VideoStream
import cv2
import matplotlib.pyplot as plt
import time
import numpy as np
import robot_io as io 
from scipy.ndimage import gaussian_filter

DEBUG = True
balloons = [None, None, None]

blue = 177
green = 57
red = 107

masks_lower = [(h-20, 124, 100) for h in (blue, green, red)]
masks_upper = [(h+20, 255, 255) for h in (blue, green, red)]

stream = VideoStream(src=0, usePiCamera=True, framerate=40).start()

'''
State machine
PATROL: drive straight until encounters a wall or sees a balloon
TURNING: turn so that the wall is no longer detected.
REVERSING: reverse and turn around
FOUND_BALLOON: turn towards balloon and accelerate
STOPPED: button toggles between STOPPED and PATROL
'''
state = "stopped"
print("Robot running")

try:
    while True:
        frame = stream.read()
        if frame is not None:
            frame = frame[80:,:,:] #crop off the top 80 pixels
            blurred = cv2.GaussianBlur(frame, (11, 11), 0)
            hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
            masks = [cv2.inRange(hsv, mask_lower, mask_upper) for
                     mask_lower, mask_upper in zip(masks_lower, masks_upper)]
            balloons = [None, None, None]
            for channel, mask in enumerate(masks):
                #red green blue
                chan = ['red','green','blue'][channel]
                circle_colour_bgr = [(0,0,255),(0,255,0),(255,0,0)][channel]
                masked = cv2.bitwise_and(frame, frame, mask=mask)
                if mask.sum() > 150000:
                    # if chan == 'green': print(mask.sum())
                    dat = mask.mean(axis=0)
                    if (dat==255).sum() > 160:
                        # balloon right in front!
                        peak = 320//2
                        height = 1000
                    else:
                        smoothed = gaussian_filter(dat, 25)
                        peak = int(np.argmax(smoothed))
                        height = int(max(smoothed))
                    cv2.circle(masked, (peak, 80), height//5, (255,255,255), 2)
                    # normalise the peak to a number between -1 and 1
                    peak = (peak - 160)/160
                    balloons[channel] = (peak, height)
                if DEBUG:
                    cv2.imshow(chan, masked)
            if DEBUG:
                cv2.imshow("Live", frame)
        else:
            pass
        if balloons[0] is not None:
            io.move(0,balloons[0][0])
        else:
            io.move(0,0)

        # check for obstacles
        found_obstacles = io.read_sensors() < 0.2
        print(found_obstacles)
        
        # check button
#         if state != "stopped" and ():
#             state = "stopped"
#             # io.beep(1)
#             
#         if state == "stopped":
#             move(0,0)
#             led_pwm.stop()
#             GPIO.output(LEDPIN, 1)
#             if GPIO.input(BUTTONPIN)==0:
#                 print("button pressed")
#                 state = "patrol"
#                 for i in range(5):
#                     beep(0.1)
#                     time.sleep(0.2)
#         elif state == "patrol":
#             move(100, 0)
#             led_pwm.start(50)
#             led_pwm.ChangeFrequency(2)
#             if any(found_obstacles):
#                 state = "turning"
#         elif state == "turning":
#             led_pwm.ChangeFrequency(1)
#             if all(found_obstacles):
#                 state = "reversing"
#             else:
#                 beep(0.05)
#                 if found_obstacles[0]: #turn to the right
#                     move(100, 50)
#                 elif found_obstacles[1]:
#                     move(100, -50)
#                 else:
#                     state = "patrol"
#         elif state == "reversing":
#             # reverse for 2 seconds
#             for i in range(2):
#                 beep(0.5)
#                 move(-100, 0)
#                 time.sleep(0.5)
#             move(0,-100)
#             time.sleep(0.5)
#             state = "patrol"
#         time.sleep(0.05)
#         print(state, time.time())
        
finally:
    cv2.destroyAllWindows()
    stream.stop()
    io.move(0,0)
