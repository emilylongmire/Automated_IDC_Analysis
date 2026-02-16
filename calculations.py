# This script will calculate RGB, brightness difference, and other values that will be added as
# columns to IDCSubmersion.csv

import pandas as pd
import numpy as np
import cv2

# read in and merge IDCSubmersion.csv on board_id if another csv is created when measuring
# (not yet tested)

# link images (video frames) to each board and calculate RGB and brightness difference

# other necessary calculations and cleaning