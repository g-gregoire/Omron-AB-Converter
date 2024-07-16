# parse entries from a .xlsx file, go through the table and add the text in column G to an array if the corresponding cell in column C is true
import os
import re
import pandas as pd
import pprint as pp

filename = "phase-matrix.xlsx" #use if nothing given by main file

# THIS NEEDS TO BE CHANGED IF ANY COLUMNS GET ADDED/REMOVED IN THE SPREADSHEET
EM_STARTING_COL = 12
  
def parseList(filename="", input_dir=""):

    if filename == "":
        filename = "PLC_Tags_IDH.xlsx" #use if nothing given by main file
    # Give the location of the file 
    
    # Set input dirt
    if input_dir == "": input_dir = os.getcwd()
    os.chdir(input_dir)
    file = os.path.join(input_dir, filename)
    
    # To open Workbook 
    # List of Symbols with either Tagnames or Descriptions
    global_symbols = pd.read_excel(file, sheet_name = 1)
    global_symbols = global_symbols.fillna('')
    # print(global_symbols.head())

    # Full list of all tags used in program
    full_taglist = pd.read_excel(file, sheet_name = 2)
    full_taglist = full_taglist.fillna('')
    # print(full_taglist.head())
    
    taglist = []

    ## VARIOUS TYPES OF TAGS 
    # address = "a120.011" # Does not exist
    # address = "120.01" # With Symbol and description
    # address = "CNT06100" # With symbol, no description
    # address = "11.04" # With Description, no symbol
    # address = "0.01" # No symbol or description
    # address = "100" # Word tag, not bit
    # address = "TIM069(bit)" # Symbol with (bit)
    # address = "HR01.00" # Weird tag structure

    # Iterate through each row of the table
    for rowindex, row in full_taglist.iterrows():
        # print(rowindex)
        
        address = row["Address"].replace("(bit)","")
        # print(address)
        if address.isnumeric():
            query = global_symbols.query(f'Address == {address}')
        else:
            query = global_symbols.query(f'Address == "{address}"')
        # print(query)
    
        if query.empty:
            # print("Tag does not have symbol or description")
            symbol = ""
            description = ""
        else:
            # print("Tag found")
            symbol =  query["Symbol"].to_string(index=False)
            description = query["Description"].to_string(index=False)


        # Try to determine type of tag
        tagType = typeFinder(row["Address"], query)

        if symbol == "":
            symbol = nameCreator(address, symbol, description)
        
        taglist.append({
            "address" : address,
            "symbol" : symbol,
            "description" : description,
            "type" : tagType
        })
        
        # print(taglist)
        # break # Break to only run first one
    

    # pp.pprint(taglist)
    # for phase in phases:
        # print(phase.name, phase.description, " Steps: ", phase.steps)
    
    return taglist

def nameCreator(address:str, symbol="", description=""):
    if symbol != "": # Use symbol if it exists already
        return symbol.upper()
    if symbol == "" and description == "": # If none exist, create tagname from address
        tagname = "ADDR-" + address.replace(".", "_")
    if symbol == "" and description != "": # If only description, create tagname from description
        split = description.upper().replace(".", "").split()[:4]
        tagname = ""
        for word in split:
            if word == split[-1]: tagname += word
            else: tagname = tagname + word + "_"
    return tagname


def typeFinder(address:str, tagQuery):
    if address.find("(bit)") >= 0: # Deal with explicit Bit definitions first
        return "BOOL"
    if not tagQuery.empty: # Use Type if already specified
        return tagQuery["Type"].to_string(index=False)
    if address.find(".") >= 0: # If there's a '.' then it's a Bool
        return "BOOL"
    if address.isnumeric(): # If it's a full number (ie. 120), then it's an INT (or word)
        return "INT"
    if address.find("DM") >= 0: # If it's a DMxxx tag, then it's an INT/word
        return "INT"
    
    # If nothing catches, return "UNKNOWN"
    return "UNKNOWN"
    
    
    

        

#%% Execute code

# phases = parseList(filename)

# # Test display for a single phase
# index = 12

# print(phases[index].name, phases[index].description, " Steps: ", phases[index].steps)

# for step in phases[index].step_detail:
#     print(step, phases[index].step_detail[step])

# for em in phases[index].EM:
#     print(em, phases[index].EM[em])

# for alarm in phases[index].alarms:
#     print(alarm, phases[index].alarms[alarm])

# for param in phases[index].parameters:
#     print(param)



    
