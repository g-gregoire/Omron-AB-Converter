import os
import pandas as pd

import components as cmp
import routine_components as rt
import lookup as lk

# Global Variables
n = '\n'
filename = "test.L5X"

# Set directories
dir = os.getcwd()
ref_dir = os.path.join(dir, "ref")
ref_dir2 = os.path.join(dir, "Reference")
output_dir = os.path.join(dir, "output")
input_dir = os.path.join(dir, "input")

# Should not be needed
def getDirectories(curDir):
    input_dir = os.path.join(curDir, "Input")
    ref_dir = os.path.join(curDir, "Reference")
    output_dir = os.path.join(curDir, "Output")
    return curDir, input_dir, output_dir, ref_dir

def getSystemName(filename:str):
    # Gets System Name from file name
    system_name = filename.split("_")[-1].split(".")[0]
    # print(system_name)
    return system_name

def createFile(filename="code.txt", input_filename="", simple_output=False):
    # Set output dir
    os.chdir(output_dir)

    # Test open and write a file
    # Delete and then open a file for writing
    try: os.remove(filename)
    except: pass

    if input_filename != "":
        systemName = getSystemName(input_filename)
        filename = systemName + "_" + filename
    else:
        filename = filename

    file = open(filename,"w") 

    if simple_output:
        filename2 = "simple_output.txt"
        file2 = open(filename2,"w") 
        return file, file2
    else:   
        return file, None

def create_plc_tag_import_file(system_name="IDH"):

    # Set output dirt
    os.chdir(output_dir)

    system_name = getSystemName(system_name)
    filename = system_name + "_PLC_tag_import.csv"

    # Test open and write a file
    # Delete and then open a file for writing 
    try: os.remove(filename)
    except: pass
    
    file = open(filename,"w") 

    # Write header
    os.chdir(ref_dir)
    f = open(lk.tagcsv, "r")
    file.write(f.read())
    file.write(n)

    return file

# Create a lookup table for PLC, HMI tags based on taglist
def createLookupTable(tagList:list, output_filename, system_name):
    # Set output dir
    os.chdir(output_dir)
    filename = system_name + "_lookup_table.csv"

    # Delete if already exists
    try: os.remove(filename)
    except: pass

    # Conver taglist to DataFrame
    tagList = pd.DataFrame(tagList)
    # Create Excel file
    tagList.to_csv(filename, index=False)
    
    # print("Created tag lookup file")

    return tagList

def openFile(filename="test_rungs.txt"):

    # Give the location of the file 
    dir = os.getcwd()
    # input_dir = os.path.join(dir, "input")
    file = os.path.join(input_dir, filename)
    
    # Open Workbook 
    if filename.find("rungs") >= 0:
        wb = pd.read_csv(file, sep='      ', header=None, engine='python')
        wb.columns = ['logic']
    elif filename.find(".csv") >= 0:
        wb = pd.read_csv(file, header=0, engine='python')
        wb = wb.fillna('')
    else:
        wb = pd.read_csv(file, sep='      ', header=None, engine='python')
        wb.columns = ['logic']

    # print(wb.head())
    return wb

def prepareFile(logic_file: pd.DataFrame):
    # This function brute force removes everything except the Mnemonic section
    # Find row for <MNEMONIC> and remove everything before it
    # Find row for </MNEMONIC> and remove everything after it
    # Write the remaining to a new file
    # Return the new file
    start = None
    for index, row in logic_file.iterrows():
        if "<MNEMONIC>" in row['logic']:
            start = index
            # break
        if "</MNEMONIC>" in row['logic']:
            end = index
            # break
    # print("Start: ", start)
    # print("End: ", end)
    
    # Update file range
    if not start: return logic_file
    logic_file = logic_file[start+1:end]
    # print(logic_file.head())
    # print(logic_file.tail())

    return logic_file

# To be completed
def addContext(file, system_name:str):
    # Change to Reference folder
    os.chdir(ref_dir)

    # Write file header
    f = open(lk.header, "r")
    text = f.read()
    text = text.replace("_system_", system_name)
    file.write(text)
    file.write(n)

    return file

# To be completed
def addFooter(file):
    # Write footer
    os.chdir(ref_dir)

    f = open(lk.footer, "r")
    file.write(f.read())
    file.write(n)

    return file

# Specific routine logic
def addRung(file, simple_file, r_num, logic, comment=None):
    text =cmp.r_start.replace("r_num", str(r_num)) + n
    
    # If comment, add comment
    if comment != None:
        text+=cmp.r_comment_start + comment +cmp.r_comment_end + n
    
    # Add Logic
    text +=cmp.r_logic_start + logic +cmp.r_logic_end + n

    # Add routine closure
    text +=cmp.r_end
    
    # Write full logic with context to file
    file.write(text)
    file.write(n)

    # Just write the logic and newline to simple file
    simple_file.write(logic + ";" + n)
    r_num += 1

    return r_num

def addTag(full_tag, file):
    # print(tag, desc, type)

    tag = full_tag["tagname"]
    desc = full_tag["description"]
    type = full_tag["tag_type"]
    alias = full_tag["alias"]

    if alias != "":
        text = rt.new_tag_alias.replace(rt.tag, tag).replace(rt.desc, desc).replace(rt.base_tag, alias)
    elif type == "REAL":
        text = rt.new_tag_float.replace(rt.tag, tag).replace(rt.desc, desc).replace(rt.type, type)
    elif type == "TIMER":
        text = rt.new_tag_timer.replace(rt.tag, tag).replace(rt.desc, desc).replace(rt.type, type)
    elif type == "COUNTER":
        text = rt.new_tag_counter.replace(rt.tag, tag).replace(rt.desc, desc).replace(rt.type, type)
    else:
        text = rt.new_tag.replace(rt.tag, tag).replace(rt.desc, desc).replace(rt.type, type)
    
    file.write(text)
    file.write(n)

    return file

def getSystemName(filename:str):
    # Gets System Name from file name
    system_name = filename.split("_")[0].split(".")[0]
    return system_name

#%% Testing - Functions
# wb = openFile()
# # print(wb.head())
# for rowindex, row in wb.iterrows():
#     print(row['logic'])