# This script simultaneously controls the source meters and raspberry pi camera
# and links the data from the user-inputted IDCSubmersion.csv

# Necessary Libraries --------------------------------------------------------------------------------------------------

import paramiko
import threading
import time
import msvcrt
import xtralien
import pandas as pd
from queue import Queue

# Pre-Submersion -------------------------------------------------------------------------------------------------------
devices = [{"host": "raspberrypi.local", "user": "pi", "pass": "password", "folders": ["Cam_1", "Cam_2"]},
           {"host": "raspberrypi2.local", "user": "pi", "pass": "password", "folders": ["Cam_3", "Cam_4"]}]

source_meter_names = ["COM4", "COM5"]
data_csv_path = "IDCSubmersion.csv"

# promts the user to enter the board_ID of the board about to be submerged
# as well as the custom file label for this submersion
# ** CHANGE TO STRICT FILE NAME FOR CONSISTENCY
try:
    data = pd.read_csv(data_csv_path)
    board_id = str(input("Enter the board ID of the board you are submerging: "))
    submersion = data[data["board_id"] == board_id]

    if submersion.empty:
        raise ValueError("Board ID not found in CSV.")

    voltage = float(submersion["voltage"].iloc[0])

    # file label (for now)
    user_label = input("Enter the custom file label: ")

except Exception as e:
    print(f"Setup Error: {e}")
    exit()


# Control Devices --------------------------------------------------------------------------------------------------------------------------

# function that starts the raspberry pi cameras
def start_remote_cameras(device, label):
    f1, f2 = device["folders"]

    # stops when you press 'q'.
    # use "nohup" (Duration set to 1 hour (-t 3600000)) and "disown" so that cams stay on after script stops running
    # ** CHANGE 1 HOUR DURATION TO LONGER IN CASE A SUBMERSION TAKES > 1 HR

    cmd = (f"TS=$(date +%Y-%m-%d_%H-%M-%S) && "
           f"mkdir -p /home/pi/{f1} /home/pi/{f2} && sleep 1 && "
           f"nohup /usr/bin/rpicam-still --camera 0 -t 3600000 --timelapse 1000 -n -o /home/pi/{f1}/\"$TS\"_{label}_%d.jpg > /home/pi/cam0_debug.txt 2>&1 & "
           f"nohup /usr/bin/rpicam-still --camera 1 -t 3600000 --timelapse 1000 -n -o /home/pi/{f2}/\"$TS\"_{label}_%d.jpg > /home/pi/cam1_debug.txt 2>&1 & "
           f"disown -a")

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(device["host"], username=device["user"], password=device["pass"])
        client.exec_command(cmd)
        time.sleep(2)
        client.close()

    except Exception as e:
        print(f"SSH Error on {device['host']}: {e}")


# function that stops the raspberry pi cams
def stop_remote_cameras(device):
    # sends the kill signal to the pis
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(device["host"], username=device["user"], password=device["pass"])
        client.exec_command("pkill rpicam-still")
        client.close()

    except:
        pass


# Threading ------------------------------------------------------------------------------------------------------------

def instrument_thread(device_name, device_index, data_queue, volt, stop_event):
    try:
        with xtralien.Device(device_name) as device:
            # Enable both channels
            device.smu1.set.enabled(True)
            device.smu2.set.enabled(True)
            print(f"Connected: {device_name} (SMU1 & SMU2 Enabled)")

            while not stop_event.is_set():
                # Measure Channel 1
                res1 = device.smu1.oneshot(volt)

                # v1 = res1[0] if isinstance(res1, (list, tuple)) else volt
                # i1 = res1[1] if isinstance(res1, (list, tuple)) else res1

                data_queue.put({
                    "timestamp": time.time(),
                    "meter": device_name,
                    "channel": "SMU1",
                    "Voltage": res1[0, 0],
                    "Current": res1[0, 1]
                })

                # Measure Channel 2
                res2 = device.smu2.oneshot(volt)

                # v2 = res2[0] if isinstance(res2, (list, tuple)) else volt
                # i2 = res2[1] if isinstance(res2, (list, tuple)) else res2

                data_queue.put({
                    "timestamp": time.time(),
                    "meter": device_name,
                    "channel": "SMU2",
                    "Voltage": res2[0, 0],
                    "Current": res2[0, 1]
                })

                time.sleep(0.1)

            # Cleanup
            device.smu1.set.enabled(False)
            device.smu2.set.enabled(False)

    except Exception as e:
        print(f"Error on {device_name}: {e}")


stop_event = threading.Event()
data_queue = Queue()

# initialize source meter data storage
source_meter_data = []

print(f"\n--- Starting Process ---")

# start the cameras first:
for d in devices:
    threading.Thread(target=start_remote_cameras, args=(d, user_label)).start()

print("Cameras triggered on Raspberry Pis.")

# start source meters second:
for i, dev_name in enumerate(source_meter_names):
    threading.Thread(target=instrument_thread, args=(dev_name, i, data_queue, voltage, stop_event), daemon=True).start()

print("Source Meters started on Windows.")
print("\n>>> RECORDING STARTED. PRESS 'q' TO STOP EVERYTHING <<<")

# pull data from queue to main list, shut down if q is pressed
try:
    while True:

        # check if 'q' key has been pressed
        if msvcrt.kbhit():
            if msvcrt.getch().decode('utf-8').lower() == 'q':
                print("\n'q' detected. Shutting down...")
                break

        while not data_queue.empty():
            source_meter_data.append(data_queue.get())

        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nManual Keyboard Interrupt detected.")

stop_event.set()

# stop the cameras
for d in devices:
    # threading.Thread(target=stop_remote_cameras, args=(d,)).start()

    # try new method
    stop_remote_cameras(d)

# save source meter data to csv
if source_meter_data:
    df = pd.DataFrame(source_meter_data)
    filename = f"{user_label}_source_meter_data.csv"
    df.to_csv(filename, index=False)
    print(f"Saved Source Meter data to: {filename}")

print("All systems stopped. Use FileZilla to collect camera images.")