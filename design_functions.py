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

def save_overwrites_of_frames(
                              updated_df,
                              original_df,
                              relevant_columns,
                              overwrites_csv_file=None,
                              ):
    if len(original_df.columns) > 3:
        current_frames = original_df.columns[3:]
        new_frames = list(set(relevant_columns).difference(current_frames))
    for index, row in updated_df.iterrows():
        if row['Value'] == "various":
            # If the user has modified it, we keep it as is (do nothing)
            if len(original_df.columns) == 3:
                continue
            if len(new_frames) > 0:
                original_df.loc[index, new_frames] = original_df['Value'][index]
        else:
            # Update original DataFrame with the new value
            original_df.loc[index, relevant_columns] = row['Value']
    if overwrites_csv_file and Path(overwrites_csv_file).parent.exists():
        original_df.to_csv(overwrites_csv_file, index=False)
    return original_df