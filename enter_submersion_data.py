# This script takes user input for upcoming IDC submersions, including the
# board ID, voltage level, solution type and concentration, and writes this
# data to a csv for further use

import pandas as pd
import os

# create an empty data frame with the necessary columns
image_data=pd.DataFrame(columns=["board_id","voltage","solution","concentration"])

# use IDCSubmersion.csv as the file to add the data to
data_file_path="IDCSubmersion.csv"

# create an initial CSV file if it doesn't exist
if not os.path.exists(data_file_path):
    image_data.to_csv(data_file_path, index=False)

# writes board ID, voltage level, solution + concentration to a csv using user inputted data
def get_image_names_and_data(data_file_path):
    # base image

    board_id=str(input("Enter Board ID (Format: 00_00_0000) :\n"))
    # future: add specific options to choose from to avoid spelling errors,
    # ex: choose from options 1-5

    voltage_level=int(input("\nChoose voltage level\n"
                            "Type 3 or 5:\n"))

    #if voltage_level!=3 or voltage_level!=5:
        #print("\nInvalid voltage level - please type 3 or 5\n")
        #voltage_level = int(input())

    solution_type=str(input("\nEnter the solution type:\n"))

    solution_concentration=int(input("\nEnter the solution concentration:\n"))

    # create a dictionary for image data
    info={"board_id" : [board_id], "voltage" : [voltage_level], "solution" : [solution_type],
          "concentration": [solution_concentration]}

    # store information in data frame
    new_data=pd.DataFrame(info)

    # add to csv
    new_data.to_csv(data_file_path, mode="a", header=False, index=False)

get_image_names_and_data(data_file_path)