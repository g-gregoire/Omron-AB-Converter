import file_functions as ff
import routine_components as rt
import parse as p
import utilities as util

import os
import pandas as pd

dir = os.getcwd()
_, input_dir, output_dir, _ = ff.getDirectories(dir)


# Unclear if used?
def createFile(phase, tagfile, output_filename=None, input_filename="IDH.csv"):

    file = ff.createFile(output_filename, input_filename)
    file = ff.addContext(file, phase)

    rnum = 0 # Initialize rung number
    snum = 1 # Initialize Section number

# Moved
# def createTags(tagList, tagFile, output_filename=None, output_ext="txt"):

#     for tag in tagList:

#         tagFile = ff.addTag(tag['tagname'], tag['description'] , tag['type'], tagFile)
#         # print(tag['symbol'], tag['description'], tag['type'])

#     tagFile.close()

#     return tagFile

def createSCADAoutput(system_name, scada_taglist, tag_lookup): 

    _, input_dir, output_dir, _ = ff.getDirectories(dir)

    # Create SCADA output file
    scada_output_name = "SCADA_lookup.csv"
    scada_output_file = ff.createFile(scada_output_name, system_name)

    # print(tag_lookup.head())

    # Loop through SCADA input file and write to SCADA output file
    for index, row in scada_taglist.iterrows():
        # print(row)
        # scada_output_file.write(row['Tag Name'] + "," + row['Description'] + "\n")
        address = row['Clean_Address']
        # print(address)

        # Convert to PLC Address and then lookup new address
        plc_address = util.scadaToPlcAddress(address)
        # print(plc_address)

        # Lookup new address in tag_lookup
        query = tag_lookup.loc[tag_lookup['address'] == plc_address]
        if not query.empty:
            tag = query["tagname"].to_string(index=False)
            # print(tag)

        # Write tagname to New_Addres column
        scada_taglist.at[index, 'New_Address'] = tag

        # break
    
    # Save the new SCADA taglist
    # print(scada_taglist.head())
    scada_taglist.to_csv(scada_output_file, index=False)

    return scada_taglist

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

def updateScadaTags(subtables, scada_lookup):
    PLC_GATEWAY = "ABR_Central.Central." # Central PLC gateway prefix for iFix
    for subtable in subtables:
        for rowindex, row in subtable.iterrows():
            if row["TAG"] == "A_TAG": continue # Skip second header row
            tagname = row["TAG"]
            address = row["I/O ADDRESS"]
            # print(tagname)
            # print(address)
            try: query = scada_lookup.query(f'TAG == "{tagname}"')
            except: query = scada_lookup.query(f'TAG == {tagname}')
            if not query.empty:
                # print(query)
                new_address = PLC_GATEWAY + query["New_Address"].to_string(index=False)
                # print(new_address)
                # Update the I/O ADDRESS with the new address and new tagname
                subtable.at[rowindex, 'I/O ADDRESS'] = new_address
                subtable.at[rowindex, 'TAG'] = "CP_" + tagname
        break
    
    return subtables

def regroupScadaTables(system_name, subtables):
    # Save to csv file
    filename = "SCADA_tag_import.csv"
    scada_updated_file = ff.createFile(filename, system_name)
    # Repeatedly write the subtable to csv, followed by a newline in the css
    for subtable in subtables:

        subtable.to_csv(scada_updated_file, mode='a', index=False)
        scada_updated_file.write("\n")

    # print("Created SCADA import file")
    
    # combined_table.to_excel(combined_output_path, index=False)

