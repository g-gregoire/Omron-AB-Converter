import os
import pandas as pd

import components as cmp

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
    
    # To open Workbook 
    # wb = pd.read_excel(file) 
    # wb = pd.read_excel(file, sheet_name = 0)
    wb = pd.read_csv(file, sep='      ', header=None, engine='python')
    wb.columns = ['logic']
    return wb


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