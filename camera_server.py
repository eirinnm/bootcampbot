import sys
import zmq
import time
import os
print("Loading OpenCV...")
from imutils.video import VideoStream
import cv2
os.popen('~/send_telegram.sh "launching camera server"')
# import matplotlib.pyplot as plt
import numpy as np
# import robot_io as io 
from scipy.ndimage import gaussian_filter
DEBUG = True
if len(sys.argv) > 1:
    if sys.argv[1] == 'NODEBUG':
        DEBUG = False

blue = 177
green = 57
red = 107

masks_lower = [(h-20, 124, 100) for h in (blue, green, red)]
masks_upper = [(h+20, 255, 255) for h in (blue, green, red)]

stream = VideoStream(src=0, usePiCamera=True, framerate=40).start()

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind('tcp://127.0.0.1:5556')
print("Launching server...")

try:
    while True:
        frame = stream.read()
        if frame is not None:
            frame = frame[80:,:,:] #crop off the top 80 pixels
            blurred = cv2.GaussianBlur(frame, (11, 11), 0)
            hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
            masks = [cv2.inRange(hsv, mask_lower, mask_upper) for
                     mask_lower, mask_upper in zip(masks_lower, masks_upper)]
            balloons = [(0,0), (0,0), (0,0)]
            for channel, mask in enumerate(masks):
                #red green blue
                chan = ['red','green','blue'][channel]
                masked = cv2.bitwise_and(frame, frame, mask=mask)
                if mask.sum() > 150000:
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
                    peak = int((peak - 160)/160 * 100)
                    balloons[channel] = (peak, height)
                if DEBUG: cv2.imshow(chan, masked)
            if DEBUG:
                cv2.imshow("Live", frame)
                print(balloons)
            key = cv2.waitKey(1)
            if key == 27:
                break
            ## end of frame capture
            ## Send balloon data to ZMQ server
            balloon_string = ' '.join(['%s %s' % (p, h) for (p, h) in balloons])
            socket.send_string('balloons %s' % balloon_string)
finally:
    print("Closing socket")
    socket.close()
    cv2.destroyAllWindows()
    stream.stop()
