import os
import file_functions as f
import rung_logic as rung
import parse

#%% Execute Logic

# Input Files
# input_file = 'input.xlsx' #not used

# CONSTANTS FOR FUNCTIONALITY
CREATE_TAGS = True
CREATE_EXCEL = True
CONVERT_SCADA_TAGS = True

# input_filename = "PLC_Tags_IDH.xlsx"
input_filename = "PLC_Tags_Sterilizer.xlsx"
output_filename = "tag_import"
tag_filename = "tag_lookup"
scada_input_filename = "SCADA_Tags.xlsx"

dir = os.getcwd()
base_dir, input_dir, output_dir, ref_dir = f.getDirectories(dir)


# Create file to be used for tag import
if CREATE_TAGS:
    # Create tag output file
    tagfile = f.createTagFile(output_filename, output_dir=output_dir, system_ref = input_filename)
    # Parse input file for tag information
    tagList = parse.parseList(filename=input_filename, input_dir=input_dir)
    # Create tags from List
    tagfile = rung.createTags(tagList, tagfile, output_filename)

    if CREATE_EXCEL:
        # Create Excel file for tag import
        tagfile = f.createExcel(tagList, tagfile, tag_filename, output_dir, system_ref = input_filename)

    if CONVERT_SCADA_TAGS:
        # Create Excel file for tag import
        scada_file = rung.createSCADAoutput(input_filename, scada_input_filename, input_dir=input_dir, output_dir=output_dir)


#%% Random tests

# EM={"EM05": [(1, 2), (1, 3), (1, 4)], #[[1,2, 3], ["EM05_V02_SP", "test", "test"]], 
#     "EM06": [(1, 2), (1, 3), (1, 4)] # [[1,2], ["EM06_V02_SP", "test"]], 
#     }

# for em in EM:
#     print(em)
#     for a, b in EM[em]:
#         print(a, b)