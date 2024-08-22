import os
import lookup as lk
import routine_components as rt

import pandas as pd

# Global Variables
n = '\n'
filename = "test.L5X"

dir = os.getcwd()
ref_dir = os.path.join(dir, "Reference")
output_dir = os.path.join(dir, "Output")

def getDirectories(curDir):
    input_dir = os.path.join(curDir, "Input")
    ref_dir = os.path.join(curDir, "Reference")
    output_dir = os.path.join(curDir, "Output")
    return curDir, input_dir, output_dir, ref_dir

def createfile(name="test", filetype="txt"):
    # Set output dir
    os.chdir(output_dir)
    filename = name + "." + filetype

    # Test open and write a file
    # Delete and then open a file for writing 
    try: os.remove(filename)
    except: pass
    
    file = open(filename,"w") 
    return file

def createTagFile(name="tags", filetype="txt", output_dir=""):

    # Set output dirt
    if output_dir == "": output_dir = os.getcwd()
    os.chdir(output_dir)

    filename = name + "." + filetype

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

def addTag(tag, desc, type, file):
    # print(tag, desc, type)

    # tag = tag.replace("_","")
    # desc = desc.replace("_","")
    # type = type.replace("_","")
    
    text = rt.new_tag.replace(rt.tag, tag).replace(rt.desc, desc).replace(rt.type, type)
    
    file.write(text)
    file.write(n)

    return file

def createExcel(tagList:list, file, output_filename, output_dir):
    # Set output dir
    os.chdir(output_dir)
    filename = output_filename + ".csv"

    # Test open and write a file
    # Delete and then open a file for writing 
    try: os.remove(filename)
    except: pass

    # Create Excel file
    # writer = pd.ExcelWriter(filename, engine='xlsxwriter')
    # for tag in tagList:
    #     tag.to_excel(writer, sheet_name=tag['tagname'], index=False)
    # writer.save()

    # Conver taglist to DataFrame
    tagList = pd.DataFrame(tagList)
    # Assuming df is your DataFrame
    tagList.to_csv(filename, index=False)

    return 