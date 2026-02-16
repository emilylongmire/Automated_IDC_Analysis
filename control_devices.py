# This script simultaneously controls the source meters and raspberry pi camera
# and links the data from the user-inputted IDCSubmersion.csv

import pandas as pd
# Ossila library for controlling source meters:
import xtralien
import threading
import time
import cv2
from queue import Queue

# read the csv
data=pd.DataFrame("IDCSubmersion.csv")

# user must input the board ID of the board they are submerging, which will be matched with
# the data in IDCSubmersion.csv
ID=str(input("Enter the board ID of the board you are submerging: "))
submersion=data[data["board_id"]]==ID

# use threading to control the camera and source meters simultaneously
def instrument_thread(data_queue):

    # initialize instrument(s) (source meters)
    while True:
        submersion=xtralien.measure()
        data_queue.put(submersion)


# main thread : raspberry pi camera
capture=cv2.VideoCapture(0)
data_queue=Queue()
threading.Thread(target=instrument_thread, args=(data_queue,), daemon=True).start()

while True:
    ret, frame=capture.read()
    if not ret: break

    # get latest data
    if not data_queue.empty():
        latest_data=data_queue.get()

    cv2.imshow("Camera", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

capture.release()
cv2.destroyAllWindows()

