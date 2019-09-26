import zmq
import time
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.subscribe('balloons')
socket.connect('tcp://127.0.0.1:5556')
while True:
    try:
        message = socket.recv(flags = zmq.NOBLOCK)
        parts = message.decode('ascii').split(' ')
        data = [int(p) for p in parts[1:]]
        balloons = data[0:2], data[2:4], data[4:6]
        print(balloons)
    except zmq.error.Again:
        pass
#     time.sleep(0.1)
    