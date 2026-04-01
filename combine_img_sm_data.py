# this script links the source meter data with each corresponding frame time-stamp
import pandas as pd

# read source meter data csv
source_data = pd.read_csv("source_meter_data.csv")
source_data["timestamp"] = source_data["timestamp"].astype(float)

# sort
source_data = source_data.sort_values("timestamp")

cameras=4

for cam_index in range(cameras):

    frames = pd.read_csv(f"cam{cam_index}_timestamps.csv")
    frames["timestamp"]=frames["timestamp"].astype(float)
    frames = frames.sort_values("timestamp")

    linked_devices = []

    # for each device, find the closest source meter reading per frame
    for device_index, device_data in source_data.groupby("device_index"):

        device_data = device_data.sort_values("timestamp").reset_index(drop=True)

        device_data = device_data.rename(columns={"timestamp": "source_timestamp"})

        merged = pd.merge_asof(frames, device_data[["source_timestamp", "measurement"]],
                               left_on="timestamp", right_on="source_timestamp", direction="nearest")
        merged = merged.rename(columns={"timestamp": "frame_timestamp"})

        merged["device_index"] = device_index

        merged["time_delta_ms"]=(merged["frame_timestamp"]-merged["source_timestamp"]).abs()*1000

        linked_devices.append(merged)

    result = pd.concat(linked_devices, ignore_index=True)
    result = result.sort_values(["frame_index", "device_index"])

    result.to_csv(f"cam{cam_index}_linked.csv", index=False)
    print(f"Saved cam{cam_index}_linked.csv")