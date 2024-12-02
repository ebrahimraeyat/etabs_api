from pathlib import Path
# import os, sys
from typing import Union

import pandas as pd

def get_overwrites_of_frames(
                            overwrites_csv_file: Union[Path, str],
                            frames: list,
                                ) -> pd.DataFrame:
    '''
    Get a csv file that contains the frame overwrites and a list of frame names.
    if each value of frame names is various, return various in Value column, otherwise return 
    unique value
    '''
    df = pd.read_csv(overwrites_csv_file)
    if len(df.columns) > 3: # There is saved overwrites of some frames
        current_frame_names = df.columns[3:]  # Get columns from the 4th column onwards
        relevant_columns = current_frame_names.intersection(frames)
        if len(relevant_columns) > 0:
            results = []

            for index, row in df.iterrows():
                values = row[relevant_columns].values
                unique_values = set(values)

                if len(unique_values) == 1:
                    new_value = unique_values.pop()
                    results.append([row['Item'], new_value, row['Options']])
                else:
                    new_value = "various"
                    results.append([row['Item'], new_value, row['Options'] + ',various'])
            df = pd.DataFrame(results, columns=['Item', 'Value', 'Options'])
    return df