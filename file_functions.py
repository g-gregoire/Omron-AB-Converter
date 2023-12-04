import os
import components as cmp

# Global Variables
n = '\n'
filename = "test.L5X"

dir = os.getcwd()
ref_dir = os.path.join(dir, "Reference")
output_dir = os.path.join(dir, "output")
input_dir = os.path.join(dir, "input")

def createfile(name="code", filetype="txt"):
    # Set output dir
    os.chdir(output_dir)
    filename = name + "." + filetype

    # Test open and write a file
    # Delete and then open a file for writing
    try: os.remove(filename)
    except: pass
    
    file = open(filename,"w") 
    return file

