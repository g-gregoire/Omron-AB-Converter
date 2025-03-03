# Imports
import functions as f

# tag_input_filename = "IDH_PLC_Tags.xlsx"
system_name = ["Extractor", "EXT"]
tag_info_filename = "tag_info.xlsx"
logic_input_filename = "Extractor.txt"
# logic_input_filename = "Sterilizer_no_symbols.txt"
# logic_input_filename = "IDH_no_symbols.txt"
# logic_input_filename = "basic_rungs1.txt"

tag_output_filename = "tag_import"
logic_output_filename = "output.L5X"

# CONSTANTS FOR TAG BUILDER FUNCTIONALITY
CREATE_TAGS = True
VIEW_TAGS = False
CREATE_LOOKUP = True
CONVERT_SCADA_TAGS = False

# CONSTANTS FOR CONVERSION FUNCTIONALITY
CONVERT = False # Perform conversion
VIEW_RUNGS = False # View the rungs as they are converted
COUNT_INSTR = False # Count the number & type of instructions in the file
PRINT_ERRORS = True # Print errors of failed conversions

catchErrors = None

tag_info, plc_logic_file = f.getFileContents(tag_info_filename, logic_input_filename)

# convert tags from input files and create lookup file for logic conversions
if CREATE_TAGS:
    tag_lookup, tag_import_file = f.tagConversion(system_name, tag_info, tag_output_filename, CREATE_TAGS, VIEW_TAGS, CREATE_LOOKUP, CONVERT_SCADA_TAGS)

# Convert logic file to converted output format
if CONVERT:
    f.logicConversion(logic_input_filename, tag_lookup, tag_import_file, output_filename=logic_output_filename, CONVERT=CONVERT, VIEW_RUNGS=VIEW_RUNGS, COUNT_INSTR=COUNT_INSTR, PRINT_ERRORS=[PRINT_ERRORS])

# Testing - Functions
