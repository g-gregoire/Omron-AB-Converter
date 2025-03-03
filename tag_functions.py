import file_functions as f
import routine_components as rt
import parse as p
import utilities as util

import os
import pandas as pd

dir = os.getcwd()

# Unclear if used?
def createFile(phase, tagfile, output_filename=None, input_filename="IDH.csv"):

    file = f.createFile(output_filename, input_filename)
    file = f.addContext(file, phase)

    rnum = 0 # Initialize rung number
    snum = 1 # Initialize Section number

# Moved
# def createTags(tagList, tagFile, output_filename=None, output_ext="txt"):

#     for tag in tagList:

#         tagFile = f.addTag(tag['tagname'], tag['description'] , tag['type'], tagFile)
#         # print(tag['symbol'], tag['description'], tag['type'])

#     tagFile.close()

#     return tagFile

def createSCADAoutput(system_name, scada_taglist, tag_lookup): 

    _, input_dir, output_dir, _ = f.getDirectories(dir)

    # Create SCADA output file
    scada_output_name = "SCADA_tags.csv"
    scada_output_file = f.createFile(scada_output_name, system_name)

    # Change to output Dir and Read lookup file
    lookup_filename = system_name + "_tag_lookup.CSV"
    if output_dir == "": os.chdir(output_dir)
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

