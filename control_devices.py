# This script simultaneously controls the source meters and raspberry pi camera
# and links the data from the user-inputted IDCSubmersion.csv

# Ossila library for controlling source meters:
import xtralien

import pandas as pd
import threading
import cv2
import time
from queue import Queue
from picamera2 import Picamera2

# read the csv
data=pd.read_csv("IDCSubmersion.csv")

# user must input the board ID of the board they are submerging, which will be matched with
# the data in IDCSubmersion.csv
ID=str(input("Enter the board ID of the board you are submerging: "))
submersion=data[data["board_id"]==ID]

# raise an error if the selected board id isn't found
if submersion.empty:
    raise ValueError("Board not found in CSV")

# get the voltage for the submersion
voltage=submersion["voltage"].values[0]
source_meter_data=[]

# use threading to control the camera and source meters simultaneously
def instrument_thread(data_queue, voltage):

    # initialize instrument(s) (source meters) and measure

    # put actual device name here
    with xtralien.Device("DEVICE NAME") as device:
        while True:
            # measure and use voltage as input, save
            result = device.SMU[0].measure.iv(voltage)  # pass voltage here
            data_queue.put(result)
            time.sleep(0.1)

# start camera
picam=Picamera2()
picam.start()

# use mp4 format
fourcc = cv2.VideoWriter_fourcc(*"mp4v")

# create file for strong video data, (640, 480)=resolution
out = cv2.VideoWriter("output.mp4", fourcc, 20.0, (640, 480))

# initialize latest_data and queue
latest_data=None
data_queue=Queue()

# start instrument thread, stops automatically when the program stops
threading.Thread(target=instrument_thread, args=(data_queue, voltage), daemon=True).start()

while True:
    # read frame from camera
    frame=picam.capture_array()
    frame=cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    # get latest data and match the source meter data with the current video timestamp
    if not data_queue.empty():
        latest_data = data_queue.get()
        source_meter_data.append({"timestamp": time.time(), "measurement": latest_data})

    # write the frame to the file
    out.write(frame)

    # displays the video, use q to quit
    cv2.imshow("Camera", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

pd.DataFrame(source_meter_data).to_csv("source_meter_data.csv", index=False)
picam.stop()
out.release()
cv2.destroyAllWindows()

