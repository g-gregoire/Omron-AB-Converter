# Imports
import functions as f

# tag_input_filename = "IDH_PLC_Tags.xlsx"
system_name = ["Extractor", "EXT"]
tag_info_filename = "tag_info.xlsx"
logic_input_filename = "2-Rind_Pumping.cxr"
# logic_input_filename = ["1-Extractor.cxr", "2-Rind_Pumping.cxr", "3-H_E_Scaling.cxr", "4-Revision_1.cxr", "5-Protocol_Macro.cxr", "6-Unnamed_0.cxr", "7-Centrifuge.cxr", "8-Pretreatment.cxr", "9-PRT_1.cxr", "10-PRT_2.cxr", "11-PRT_3.cxr", "12-PRT_4.cxr", "13-Acid.cxr", "14-PRT_Common.cxr", "15-PRT_IO.cxr"]
# logic_input_filename = "test_rungs.cxr" # Used to overwrite for testing
scada_tag_export_filename = "EXT_PLC_SCADA_TAGS.xlsx"
# logic_input_filename = "Sterilizer_no_symbols.txt"
# logic_input_filename = "IDH_no_symbols.txt"

tag_output_filename = "tag_import"
tag_lookup_filename = "EXT_lookup_table.csv"
logic_output_filename = "output.L5X"

# CONSTANTS FOR TAG BUILDER FUNCTIONALITY
CREATE_TAGS = False
CREATE_LOOKUP = True
CONVERT_SCADA_TAGS = False
VIEW_TAGS = False

# CONSTANTS FOR CONVERSION FUNCTIONALITY
CONVERT = True # Perform conversion
VIEW_RUNGS = True # View the rungs as they are converted
COUNT_INSTR = False # Count the number & type of instructions in the file
PRINT_ERRORS = False # Print errors of failed conversions

catchErrors = None
instr_count_total = {}


if isinstance(logic_input_filename, str):
    logic_input_filename = [logic_input_filename]

for filename in logic_input_filename:
    print("\nStarting on ", filename)
    tag_info, plc_logic_file = f.getFileContents(tag_info_filename, filename)

    # convert tags from input files and create lookup file for logic conversions
    if CREATE_TAGS:
        tag_lookup, tag_import_file = f.tagConversion(system_name, tag_info, scada_tag_export_filename, tag_output_filename, CREATE_TAGS, VIEW_TAGS, CREATE_LOOKUP, CONVERT_SCADA_TAGS)
    else: 
        try:
            tag_lookup = f.readTagLookup(tag_lookup_filename)
        except:
            tag_lookup = None
        # print(tag_lookup)
    # Convert logic file to converted output format
    instr_count_total = f.logicConversion(system_name, filename, tag_lookup, instr_count_total, output_filename=logic_output_filename, CONVERT=CONVERT, VIEW_RUNGS=VIEW_RUNGS, COUNT_INSTR=COUNT_INSTR, PRINT_ERRORS=[PRINT_ERRORS])

if COUNT_INSTR:
    print("Total Instructions: ")
    print(instr_count_total)
# Testing - Functions
