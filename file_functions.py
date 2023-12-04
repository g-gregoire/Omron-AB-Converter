import os
import components as cmp

# Global Variables
n = '\n'
filename = "test.L5X"

# Set directories
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