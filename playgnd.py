import file_functions as ff
import logic_converter as lc
import utilities as util
import lookup as lk

import os
import pandas as pd

EOL = "^^^"
NL = "\n"
dir = os.getcwd()
# Open file

scada_file = "EXT_PLC_SCADA_TAGS.xlsx"
_, input_dir, output_dir, _ = ff.getDirectories(dir)
    
def extractScadaTags(scada_file):
    # Get all directories

    # Get System Name
    system_name = ff.getSystemName(scada_file)

    # Set input dir
    os.chdir(input_dir)

    # 1. Extract PLC Tag List
    file = os.path.join(input_dir, scada_file)

    scada_tags = pd.read_excel(file, sheet_name = 0, header=None).reset_index(drop=True)
    # print(scada_tags.head())

    # Find empty rows which might separate tables
    empty_rows = scada_tags.isna().all(axis=1)
    empty_row_indices = list(empty_rows[empty_rows].index)
    # print(empty_row_indices)

    # Add start and end indices to create ranges
    table_ranges = []
    start_idx = 0

    for idx in empty_row_indices:
        if idx > start_idx:  # Only add if there's data between start_idx and idx
            table_ranges.append((start_idx, idx))
        start_idx = idx + 1

    # Add the last table if there's data after the last empty row
    if start_idx < len(scada_tags):
        table_ranges.append((start_idx, len(scada_tags)))
    # print(table_ranges)

    # Extract each subtable
    subtables = []
    for start, end in table_ranges:
        if end > start:  # Ensure there's at least one row
            subtable = scada_tags.iloc[start:end].reset_index(drop=True)
            # print(subtable.head())
            # Optionally set the first row as header
            subtable.columns = subtable.iloc[0]
            subtable = subtable.iloc[1:].reset_index(drop=True)
            subtable = subtable.fillna('')
            # subtable = subtable.reset_index(drop=True)
            subtables.append(subtable)

    
    # print(subtables[0].iloc[:, 1])
    return subtables

def updateScadaTags(subtables):
    for subtable in subtables:
        for rowindex, row in subtable.iterrows():
            if row["TAG"] == "A_TAG":
                continue
            tagname = row["TAG"]
            address = row["I/O ADDRESS"]
            print(tagname)
            print(address)
            break
        break

def regroupScadaTables(subtables, filename):
    # Save to csv file
    combined_output_path = os.path.join(output_dir, filename.split(".")[0] + "_updated.csv")

    # Repeatedly write the subtable to csv, followed by a newline in the css
    for subtable in subtables:

        subtable.to_csv(combined_output_path, mode='a', index=False)
        with open(combined_output_path, 'a') as f:
            # f.write(EOL)
            f.write(NL)

    
    # combined_table.to_excel(combined_output_path, index=False)



# Testing

subtables = extractScadaTags(scada_file)
updateScadaTags(subtables)
regroupScadaTables(subtables, scada_file)