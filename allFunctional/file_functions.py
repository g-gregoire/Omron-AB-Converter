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

def createFile(filename="code.txt", input_filename="system.txt"):
    # Set output dir
    os.chdir(output_dir)

    # Test open and write a file
    # Delete and then open a file for writing
    try: os.remove(filename)
    except: pass

    systemName = getSystemName(input_filename)
    filename = systemName + "_" + filename
    
    file = open(filename,"w") 
    return file

def createTagFile(name="tags", filetype="CSV", system_ref="IDH"):

    # Set output dirt
    os.chdir(output_dir)

    system_name = getSystemName(system_ref)
    filename = system_name + "_" + name + "." + filetype

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

def createExcel(tagList:list, output_filename, system_ref="IDH"):
    # Set output dir
    os.chdir(output_dir)
    system_name = getSystemName(system_ref)
    filename = system_name + "_" + output_filename

    # Test open and write a file
    # Delete and then open a file for writing 
    try: os.remove(filename)
    except: pass

    # Conver taglist to DataFrame
    tagList = pd.DataFrame(tagList)
    # Create Excel file
    tagList.to_csv(filename, index=False)

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
def addRung(file, r_num, logic, comment=None):
    text =cmp.r_start.replace("r_num", str(r_num)) + n
    
    # If comment, add comment
    if comment != None:
        text+=cmp.r_comment_start + comment +cmp.r_comment_end + n
    
    # Add Logic
    text +=cmp.r_logic_start + logic +cmp.r_logic_end + n

    # Add routine closure
    text +=cmp.r_end
    
    file.write(text)
    file.write(n)
    r_num += 1

    return file, r_num

def addTag(tag, desc, type, file):
    # print(tag, desc, type)

    # tag = tag.replace("_","")
    # desc = desc.replace("_","")
    # type = type.replace("_","")
    
    if type == "REAL":
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