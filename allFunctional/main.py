# Imports
import os
import file_functions as ff
import rung_logic as rung
import parse
import logic_converter as lc
import lookup as lk
import functions as mf

import traceback

# CONSTANTS FOR CONVERSION FUNCTIONALITY
CONVERT = True # Perform conversion
VIEW_RUNGS = False # View the rungs as they are converted
COUNT_INSTR = False # Count the number & type of instructions in the file
PRINT_ERRORS = True # Print errors of failed conversions

# CONSTANTS FOR TAG BUILDER FUNCTIONALITY
CREATE_TAGS = True
CREATE_EXCEL = True
CONVERT_SCADA_TAGS = True

tag_input_filename = "IDH_PLC_Tags.xlsx"
# tag_input_filename = "PLC_Tags_Sterilizer.xlsx"
scada_input_filename = "SCADA_Tags.xlsx"
tag_output_filename = "tag_import"
tag_filename = "tag_lookup" # TO DELETE

logic_input_filename = "IDH_no_symbols.txt"
# logic_input_filename = "Sterilizer_no_symbols.txt"
# logic_input_filename = "basic_rungs1.txt"
tag_filename = "tag_lookup.csv" # TO DELETE
logic_output_filename = "output.L5X"


catchErrors = None

mf.tagConversion(tag_input_filename, tag_filename, scada_input_filename, tag_output_filename, CREATE_TAGS, CREATE_EXCEL, CONVERT_SCADA_TAGS)

# mf.runConversion(logic_input_filename, tag_filename, output_filename=logic_output_filename, CONVERT=CONVERT, VIEW_RUNGS=VIEW_RUNGS, COUNT_INSTR=COUNT_INSTR, PRINT_ERRORS=[PRINT_ERRORS])

# Testing - Functions