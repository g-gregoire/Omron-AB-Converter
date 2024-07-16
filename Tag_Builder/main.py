import os
import file_functions as f
import rung_logic as rung
import parse

#%% Execute Logic

# Input Files
# input_file = 'input.xlsx' #not used

# CONSTANTS FOR FUNCTIONALITY
CREATE_PHASE_LOGIC = False
PHASE_ALARM_RESET = True
PHASE_JSR = True
CREATE_TAGS = False
PHASE_MODE_ENABLE = True

input_filename = "PLC_Tags_IDH.xlsx"
output_filename = "tag_import"
phase_nums = ["all"] # Use to select all phases
# phase_nums = ["010A",
#               "022A",
#               "042",
#               "043",
#               "049A",
#               "050A",
#               "051A",
#               "052A",
#               "053",
#               "054",
#               "055A",
#               "056A",
#               "057A"
#               ] #, "039", "040", "041"]

# Get relevant directories for functions
dir = os.getcwd()
base_dir, input_dir, output_dir, ref_dir = f.getDirectories(dir)


# Create file to be used for tag import
tagfile = f.createTagFile(output_filename, output_dir=output_dir)

tagList = parse.parseList(filename=input_filename, input_dir=input_dir)

tagfile = rung.createTags(tagList, tagfile, output_filename)


#%% Random tests

# EM={"EM05": [(1, 2), (1, 3), (1, 4)], #[[1,2, 3], ["EM05_V02_SP", "test", "test"]], 
#     "EM06": [(1, 2), (1, 3), (1, 4)] # [[1,2], ["EM06_V02_SP", "test"]], 
#     }

# for em in EM:
#     print(em)
#     for a, b in EM[em]:
#         print(a, b)