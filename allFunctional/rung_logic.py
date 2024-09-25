import file_functions as f
import routine_components as rt

import os
import pandas as pd
import parse as p

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

def createSCADAoutput(input_filename, scada_filename): 

    _, input_dir, output_dir, _ = f.getDirectories(dir)

    # Set input dir
    os.chdir(input_dir)
    file = os.path.join(input_dir, scada_filename)

    # Get system name
    system_name = f.getSystemName(input_filename)
    # print(input_filename)
    
    # Create SCADA output file
    scada_output_name = "SCADA_tags.csv"
    scada_output_file = f.createFile(scada_output_name, system_name)

    # Read SCADA input file
    if system_name == "IDH":
        scada_taglist = pd.read_excel(file, sheet_name = 1)
    elif system_name == "Sterilizer":
        scada_taglist = pd.read_excel(file, sheet_name = 3)
    else:
        scada_taglist = pd.read_excel(file, sheet_name = 0)
    scada_taglist = scada_taglist.fillna('')
    # print(scada_taglist.head())

    # Change to output Dir and Read lookup file
    lookup_filename = system_name + "_tag_lookup.CSV"
    if output_dir == "": os.chdir(output_dir)
    tag_lookup = pd.read_csv(lookup_filename)
    tag_lookup = tag_lookup.fillna('')
    # print(tag_lookup.head())

    # Loop through SCADA input file and write to SCADA output file
    for index, row in scada_taglist.iterrows():
        # print(row)
        # scada_output_file.write(row['Tag Name'] + "," + row['Description'] + "\n")
        address = row['Clean_Address']
        # print(address)

        # Convert to PLC Address and then lookup new address
        plc_address = p.scadaToPlcAddress(address)
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

