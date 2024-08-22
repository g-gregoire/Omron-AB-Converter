import os
import pandas as pd

import components as cmp

import xml.etree.ElementTree as ET

# Global Variables
n = '\n'
filename = "test.L5X"

# Set directories
dir = os.getcwd()
ref_dir = os.path.join(dir, "Reference")
output_dir = os.path.join(dir, "output")
input_dir = os.path.join(dir, "input")

def createFile(name="code", filetype="txt"):
    # Set output dir
    os.chdir(output_dir)
    filename = name + "." + filetype

    # Test open and write a file
    # Delete and then open a file for writing
    try: os.remove(filename)
    except: pass
    
    file = open(filename,"w") 
    return file

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
def addContext(file, phase):
    pass

# To be completed
def addFooter(file):
    pass

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


# Testing - Functions
# wb = openFile()
# # print(wb.head())
# for rowindex, row in wb.iterrows():
#     print(row['logic'])