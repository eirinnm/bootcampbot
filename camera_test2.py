from imutils.video import VideoStream
import cv2
import matplotlib.pyplot as plt
import time
import numpy as np
import robot_io as io 
from scipy.ndimage import gaussian_filter
# redLower = (145,128,120)
# redUpper = (183,255,255)
# greenLower = (44,114,94)
# greenUpper = (76,255,255)
# blueLower = ()
blue = 177
green = 57
red = 107
# hsv_lower = (50, 124, 100)
# hsv_upper = (200, 255, 255)
masks_lower = [(h-20, 124, 100) for h in (blue, green, red)]
masks_upper = [(h+20, 255, 255) for h in (blue, green, red)]

vs = VideoStream(src=0, usePiCamera=True, framerate=40).start()
time.sleep(0.5)
try:
    while True:
        frame = vs.read()
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
            cv2.imshow(chan, masked)
        cv2.imshow("Live", frame)
        key = cv2.waitKey(1)
        if key == 27:
            break
finally:
    cv2.destroyAllWindows()
    vs.stop()
    io.move(0,0)