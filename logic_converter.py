import file_functions as ff
import lookup as lk
import utilities_logic as ul
from structures import Routine, Rung, Block
from typing import List

import pandas as pd
from pprint import pprint
import re


EOL = "^^^"
NL = "\n"
SP = " "
END = ";"

# To be used as global variables
one_shot_index = 0

def extract_rungs(logic_file: pd.DataFrame):
    # This function extracts the rungs from the logic file and creates a routine object
    routine = Routine()
    rung = Rung()
    rung_text = ""
    comment = ""
    for rowindex, row in logic_file.iterrows():
        rung_text, comment, end_of_rung, BREAK = get_rung(row['logic'], rung_text, comment)
        if end_of_rung:
            rung.addOriginal(rung_text)
            routine.addRung(rung)
            if comment != "":
                rung.addComment(comment)
            
            # Reset variables
            rung = Rung()
            rung_text = ""
            comment = ""
        if BREAK: break
    
    # routine.viewRungs()
    return routine

def loop_rungs_v2(routine: Routine, tagfile: pd.DataFrame, system_name:str):
    # This function converts the rungs in a routine
    catchErrors = {
        "count": 0,
        "list": [],
        "error": False
    }
    for rung in routine.rungs:
            # _, catchErrors = blockBreaker(rung, catchErrors)
            rung, _ = block_breaker_v2(rung, catchErrors)
            rung.viewBlocks()
            rung, catchErrors = convert_blocks(rung, catchErrors, tagfile, system_name)
            rung.viewBlocks()
            rung = block_assembler_v2(rung)
            rung.viewBlocks()
            
            
        
    return routine, catchErrors

def block_breaker_v2(rung: Rung, catchErrors: dict):
    # This function splits rung into logic/load blocks
    rung_text = rung.original
    rung_array = rung_text.split(NL)[:-1]
    current_details = []
    current_block_type = ""
    blocks_in = 1
    DEBUG_bbv2 = False

    # Loop through each instruction in the rung_text
    for index, line in enumerate(rung_array):
        instr, params, details = ul.expand_instruction(line)
        if DEBUG_bbv2: print(index, details)
        block_type = details["block_type"]
        details_add = details.copy() # Need to create copy due to dictionary reference

        if block_type == "INTER" and current_details != []: # ANDLD or ORLD, with a current block
            if DEBUG_bbv2: print("-", 1, current_details)
            # Log the current block before continuing
            rung.addBlock(Block(current_details, current_type, blocks_in))
            current_details = []
            # Continue and immediately log ANDLD/ORLD block
            rung.addBlock(Block([details_add], block_type, details["blocks_in"]))
            current_details = []
            
        elif block_type == "INTER" and current_details == []: # ANDLD or ORLD, with no current block (ie back-to-back ANDLD/ORLD)
            if DEBUG_bbv2: print("-", 1, current_details)
            # Continue and immediately log ANDLD/ORLD block
            rung.addBlock(Block([details_add], block_type, details["blocks_in"]))
            current_details = []

        elif block_type == "START" and current_details == []: # LD-type instruction and no current block
            current_details.append(details_add)
            current_type = block_type
            if DEBUG_bbv2: print("-", 2, current_details)

        elif block_type == "START" and current_details != []: # LD-type instruction with an existing block
            if DEBUG_bbv2: print("-", 3, current_details)
            # Log the current block before continuing
            rung.addBlock(Block(current_details, current_type, blocks_in))
            current_details = []
            # Continue
            current_details.append(details_add)
            current_type = block_type

        elif block_type == "OUT" and current_details == []: # Output-type instruction and no current block
            if DEBUG_bbv2: print("-", 4, current_details)
            # Immediately log output block
            rung.addBlock(Block([details_add], block_type, details["blocks_in"]))
            current_details = []

        elif block_type == "OUT" and current_details != []: # Output-type instruction with an existing block
            if DEBUG_bbv2: print("-", 5, current_details)
            # Log the current block before continuing
            rung.addBlock(Block(current_details, current_type, blocks_in))
            current_details = []
            # Continue and immediately log output block
            rung.addBlock(Block([details_add], block_type, details["blocks_in"]))
            current_details = []
            
        elif block_type == "IN" or block_type == "OR": # Standard instruction
            current_details.append(details_add)
            current_type = block_type
            blocks_in = details["blocks_in"]
            if DEBUG_bbv2: print("-", 6, current_details)

        # Catch the last block
        if index == len(rung_array) - 1 and current_details != []:
            if DEBUG_bbv2: print("-", 7, current_details)
            rung.addBlock(Block(current_details, current_type, blocks_in))
            current_details = []
        
    return rung, catchErrors

def convert_blocks(rung: Rung, catchErrors: dict, tagfile: pd.DataFrame, system_name:str):
    # This function converts the blocks in a rung
    for index, block in enumerate(rung.blocks):
        # print("Block:", block)

        # Loop through each instruction in the block
        for index, line in enumerate(block.converted_block):
            # print("Line:", line)
            instr, params, details = ul.expand_instruction(line)

            # Convert the instruction
            converted_instruction, catchErrors = convertInstruction(line, catchErrors, tagfile, system_name)
            if catchErrors["error"]: 
                rung.comment += f" - ERROR CONVERTING THIS RUNG ({instr})."
                catchErrors["error"] = False

            # Update the converted_block and details["logic"] with the converted instruction
            block.converted_block[index] = converted_instruction
            block.details[index]["logic"] = converted_instruction
            # print(converted_instruction)

    return rung, catchErrors

def block_assembler_v2(rung: Rung):
    # This function reassemble the blocks into a rung
    # Steps: 

    # FORWARD PASS - handle basic inner joins
    for index, block in enumerate(rung.blocks):
        # print(block.details)
        if len(block.logic) > 1: # Join simple blocks
            block.innerJoin()
        else: # Single line block -> set to converted_logic
            block.converted_block = block.logic
    # rung.viewBlocks()

    # FORWARD PASS - handle ANDLD and ORLD blocks
    index = 0
    while index < len(rung.blocks): # Could be improved - multiple ORLD creates multiple nested branches
        block = rung.blocks[index]
        # print(index, block, block.block_type)
        if block.block_type == "INTER":
            if block.details[0]["instr"] == "ANDLD":
                rung.blocks.pop(index) # Remove the ANDLD block
                rung.join2Blocks(index-2, index-1, "AND") # Join the previous 2 blocks
                index = 0 # Reset counter since we popped a block
                # print("End: ", rung.blocks[index-1], NL)
                continue
            elif block.details[0]["instr"] == "ORLD":
                rung.blocks.pop(index) # Remove the ORLD block
                rung.join2Blocks(index-2, index-1, "OR") # Join the previous 2 blocks
                index = 0 # Reset counter since we popped a block
                # print("End: ", rung.blocks[index-1], NL)
                continue

        index += 1
    
    # Check if multiple OUT-type blocks exist
    multiple_count = 0
    for block in rung.blocks:
        if block.block_type == "OUT":
            multiple_count += 1
    if multiple_count > 1:
        multiple_OUT = True
    else:
        multiple_OUT = False
            
    # REVERSE PASS - handle output-type blocks and remaining joins
    index = 0
    working_logic = []
    active_OR = False
    for index, block in enumerate(reversed(rung.blocks)):
        
        # Get working variables
        logic = block.converted_block
        block_type = block.block_type
        # print(index, block, block_type)

        # Determine previous block in array (next one in reversed array)
        try:
            prev_block = rung.blocks[-index-2]
            prev_type = prev_block.block_type
        except:
            prev_block = None
            prev_type = None

        if block_type == "OUT":
            # print("OR type. Line: ", logic)
            if multiple_OUT: # If multiple outputs, we need brackets for branches
                if active_OR == False:
                    working_logic.append("]")
                    working_logic.append(logic[0])
                    active_OR = True
                else:
                    working_logic.append(",")
                    working_logic.append(logic[0])
            else: # If single output, no brackets needed
                working_logic.append(logic[0])

        elif block_type == "START": # If start (LD) block, then close bracket is it's open
            if active_OR == False:
                working_logic.append(logic[0])
            else:
                working_logic.append("[")
                working_logic.append(logic[0])
                active_OR = False
        elif block_type == "IN": # If IN block, then just add the logic normally
            if active_OR == False:
                working_logic.append(logic[0])
            else:
                working_logic.append(logic[0])
        
        # print("End: ", block)
    # print(working_logic)
    output_logic = "".join(reversed(working_logic))
    # print(output_logic)
    details = {
        "logic": output_logic,
        "block_type": "IN",
        "blocks_in": 1
    }
    block_type = "IN"
    blocks_in = 1

    # Overwrite blocks with new logic
    rung.blocks = [Block([details], block_type, blocks_in)]
    
    return rung

def loop_rungs(logic_file: pd.DataFrame, output_file, tagfile, view_rungs = False, start_rung=0, num_rungs=-1, system_name:str="Sterilizer"):
    rung = ""
    rung_num = 0
    catchErrors = {
        "count": 0,
        "list": [],
        "error": False
    }
    
    for rowindex, row in logic_file.iterrows():
        # print(rung_num)
        # Loop through each row and build the rung until the end of the rung
        rung, end_of_rung, BREAK = get_rung(row['logic'], rung)
        # print(rung)

        # Once the end of the rung is reached, decode the entire rung
        if end_of_rung:
            # print(rung)
            if rung_num <= start_rung-1:
                rung = ""
                continue # Skip to the next rung

            # Call function to break the rung into blocks
            rung_blocks, catchErrors = blockBreaker(rung, catchErrors)
            for block in rung_blocks.blocks:
                print(block)
            break
            # Call function to convert the blocks
            converted_rung, catchErrors = convert_blocks(rung_blocks, catchErrors, tagfile, system_name)
            # Call function to assemble the blocks
            converted_rung = assembleBlocks(converted_rung)
            # break

            ff.addRung(output_file, rung_num, converted_rung.converted_logic, converted_rung.comment)
            rung_num += 1
            rung = ""

            # If the view_rungs flag is set, print the rung
            if view_rungs:
                converted_rung.viewRung()

            # If the number of rungs is not specified, continue to the end of the file
            if num_rungs == -1:
                continue
            # If the number of rungs is specified, check if the number of rungs is reached
            elif rung_num >= (start_rung+num_rungs):
                print("Reached end of requested rungs")
                return
            
        if BREAK: 
            print("Exiting code at Break point.")
            print(rung)
            break
            
    return catchErrors

def countInstructions(logic_file: pd.DataFrame, instr_count_total):
    # This function counts the number of different instructions in the program,
    # and how many times each instruction is used
    rung = ""
    instr_count = {}
    for row_index, row in logic_file.iterrows():
        # print(row_index, row['logic'])
        # Loop through each row and build the rung until the end of the rung
        rung, end_of_rung = get_rung(row['logic'], "")
        instr = rung.split(' ')[0]
        # print(instr)
        # Skip on end of rung (^^^)
        if end_of_rung: continue
        # Skip on comments (')
        if instr == "'": continue
        if instr in instr_count:
            instr_count[instr] += 1
        else:
            instr_count[instr] = 1
        
        if instr in instr_count_total:
            instr_count_total[instr] += 1
        else:
            instr_count_total[instr] = 1

    # Order instructions by count (value)
    instr_count = dict(sorted(instr_count.items(), key=lambda item: item[1], reverse=True))
    instr_count_total = dict(sorted(instr_count_total.items(), key=lambda item: item[1], reverse=True))
    # Order instruction list alphabetically
    # instr_count = dict(sorted(instr_count.items(), key=lambda item: item[0]))
    print(instr_count)
    return instr_count, instr_count_total

def get_rung(text: str, rung_text: str, comment: str):
    # Check if the end of the rung_text is reached (^^^) and set the flag true
    BREAK = False
    end_of_rung = False
    if text == "BREAK": # Break point for testing
        BREAK = True
    elif text == EOL: # End of rung designator ^^^
        end_of_rung = True
    elif text[0] == "'": # Comment designator ' as first character
        # print("Comment found")
        comment = text

    # Otherwise, add the text to the rung_text and new line
    elif text == "ORLD" or text == "ANDLD":
        end_of_rung = False
        rung_text += text + " " + NL
    else: # If nothing else, add the text to the rung_text
        end_of_rung = False
        rung_text += text + NL

    return rung_text, comment, end_of_rung, BREAK

def blockBreaker(rung: Rung, catchErrors: dict):
    # This function splits rung into logic/load blocks
    rung_text = rung.original
    # print(rung)
    # Create structures to use
    # outputRung = Rung()
    startRung = False
    OUTPUT_BLOCK = False
    # Split instructions into an array; exclude the last empty string
    rung_text = rung_text.split(NL)[:-1]

    # Loop through each instruction in the rung_text
    for index, line in enumerate(rung_text):
        # print(line)
        # Extract current line
        instr, param, instr_type, conv_instr,_,_ = extractLine(line)
        
        # Skip instruction if it's CLC(41)
        if instr == "CLC(41)":
            continue

        # Extract previous line
        try: 
            prev_line = rung_text[index-1]
            prev_instr, prev_param, prev_instr_type, prev_conv_instr = extractLine(prev_line)
        except: 
            prev_line = prev_instr = prev_param = prev_instr_type = prev_conv_instr = None
        # Extract next line
        try:
            next_line = rung_text[index+1]
            next_instr, next_param, next_instr_type, next_conv_instr,_,_ = extractLine(next_line)
        except:
            next_line = next_instr = next_param = next_instr_type = next_conv_instr = None
        # Extract after next line
        try:
            after_next_line = rung_text[index+2]
            after_next_instr, after_next_param, after_next_instr_type, after_next_conv_instr,_,_ = extractLine(after_next_line)
        except:
            after_next_line = after_next_instr = after_next_param = after_next_instr_type = after_next_conv_instr = None

        # If next block is a counter, create a new block since this involves a CTU instruction and a Reset instruction
        if next_line and next_instr_type.upper() == "COUNTER":
            # print("Counter is next")
            # print(next_line)
            if len(block.logic) > 0:
                rung.addBlock(block) # Add the old block to the rung
            block = Block() # Create a new block
            new_block = Block() # Create a separate block from the current thread
            new_block.addLine(next_line)
            rung.addBlock(new_block) # Add the current output block to the rung
            block = Block()
            block.addLine("ANDLD") # This is used to artifically add an ANDLD block
            rung.addBlock(block)
            block = Block()

        # Required since the counter instruction is split into 2 lines (CTU and RES)
        if instr_type.upper() == "COUNTER":
            # print("Counter")
            line = line.replace("CNT", "RESET")
            line = line.replace(param, "CNT"+param)
            # print(line, param)
        
        if instr_type.upper() == "COMPARE":
            # print("Compare")
            if len(block.logic) > 0:
                rung.addBlock(block) # Add the old block to the rung
            block = Block() # Create a new block
            # Determine which comparison is being used
            EQU = GRT = LES = False
            if next_line == None: # Added for strange coding where CMP and comp_type are on different rungs
                # print("End of rung")
                catchErrors["error"] = True
                catchErrors["list"].append(line)
                rung.comment += f" - ERROR CONVERTING THIS RUNG ({instr})."
            else:
                if next_line.find("EQUALS") != -1 or next_line.find("P_EQ") != -1:
                    EQU = True
                elif next_line.find("GREATER_THAN") != -1 or next_line.find("P_GT") != -1:
                    GRT = True
                elif next_line.find("LESS_THAN") != -1 or next_line.find("P_LT") != -1:
                    LES = True
                if after_next_line.find("EQUALS") != -1 or after_next_line.find("P_EQ") != -1:
                    EQU = True
                elif after_next_line.find("GREATER_THAN") != -1 or after_next_line.find("P_GT") != -1:
                    GRT = True
                elif after_next_line.find("LESS_THAN") != -1 or after_next_line.find("P_LT") != -1:
                    LES = True
            
                if EQU and GRT:
                    # print("GEQ")
                    line = line.replace("CMP(20)", "GEQ")
                    # Pop next 3 lines
                    rung_text.pop(index+1)
                    rung_text.pop(index+1)
                    rung_text.pop(index+1)
                elif EQU and LES:
                    # print("LEQ")
                    line = line.replace("CMP(20)", "LEQ")
                    # Pop next 3 lines
                    rung_text.pop(index+1)
                    rung_text.pop(index+1)
                    rung_text.pop(index+1)
                elif EQU:
                    # print("EQU")
                    line = line.replace("CMP(20)", "EQU")
                    # Pop next line
                    rung_text.pop(index+1)
                elif GRT:
                    # print("GRT")
                    line = line.replace("CMP(20)", "GRT")
                    # Pop next line
                    rung_text.pop(index+1)
                elif LES:
                    # print("LES")
                    line = line.replace("CMP(20)", "LES")
                    # Pop next line
                    rung_text.pop(index+1)
                else:
                    line = line.replace("CMP(20)", "LES")
                    rung_text.pop(index+1)

        # If parameter matches pattern TRx where x is a number, using regex
        if param != None and re.match(r"TR\d", param):
            # print("TR Block")
            rung.has_TR_blocks = True
            TR_NUM = param[-1]
            # print(TR_NUM)
            if instr == "OUT":
                if len(block.logic) > 0:
                    rung.addBlock(block) # Add the old block to the rung
                block = Block() 
                block.addLine("STBR-"+TR_NUM) # This is used to artifically add an Start Branch (STBR) block
                rung.addBlock(block)
                block = Block()
                continue
            elif instr == "LD":
                if len(block.logic) > 0:
                    rung.addBlock(block) # Add the old block to the rung
                block = Block() 
                block.addLine("NWBR-"+TR_NUM) # This is used to artifically add an Start Branch (NWBR) block
                rung.addBlock(block)
                block = Block()
                continue
            # continue


        if instr == "LD" or instr == "LDNOT":
            if not startRung:
                # print("Start Rung")
                startRung = True
                block = Block()
                block.addLine(line)
                # rung.addConnector("START")
                # rung.viewRung()
            else:
                # print("New Block")
                if len(block.logic) > 0:
                    rung.addBlock(block) # Add the old block to the rung
                block = Block() # Create a new block
                block.addLine(line)

        elif instr == "OR" or instr == "ORNOT":
            # print("New Block - OR")
            if len(block.logic) > 0:
                rung.addBlock(block) # Add the old block to the rung
            block = Block()
            block.addLine(line) # This is used to add the current block
            rung.addBlock(block)
            block = Block() 
            block.addLine("ORLD") # This is used to artifically add an ORLD block
            rung.addBlock(block)
            block = Block()

        elif instr == "ANDLD" or instr == "ORLD":
            if len(block.logic) > 0:
                rung.addBlock(block) # Add the old block to the rung
            block = Block()
            block.addLine(instr)
            rung.addBlock(block)
            block = Block()

        # Keep instruction - needs to be broken up into OTL and OTU
        elif instr_type.upper() == "KEEP":
            if len(block.logic) > 0:
                rung.addBlock(block) # Add the old block to the rung
            # print("keep")
            insert_index = findLastLD(rung)
            if insert_index != -1:
                # Insert OTL instruction before the last LD instruction
                block = Block()
                block.addLine(line)
                rung.blocks.insert(insert_index, block)
                block = Block() 
                block.addLine("ANDLD") # This is used to artifically add an ORLD block
                rung.blocks.insert(insert_index+1, block)
                block = Block()
                # Insert OTU instruction in the Keep block
                block = Block()
                line = line.replace("KEEP(11)", "OTU")
                block.addLine(line)
                rung.addBlock(block) # Add the OTU block to the rung
                block = Block() 
                block.addLine("ANDLD") # This is used to artifically add an ORLD block
                rung.addBlock(block)
                block = Block()
                block.addLine("ORLD") # This is used to artifically add an ORLD block
                rung.addBlock(block)
                block = Block()

        # Manage output-type instructions
        elif instr_type.upper() == "OUTPUT" or instr_type.upper() == "ONESHOT" or instr_type.upper() == "TIMER" \
            or instr_type.upper() == "COUNTER" or instr_type.upper() == "MATH" or instr_type.upper() == "LOGICAL"\
            or instr_type.upper() == "COPY" or instr_type.upper() == "SCALING" or instr_type.upper() == "PID"\
            or instr_type.upper() == "BTD" or instr.upper() == "BIN(23)" or instr.upper() == "BCD(24)":
            # print("New Block - output type")
            # Counter type needs to be handled specially
            if instr_type.upper() == "COUNTER":
                # print(1)
                block.addLine(line)
                rung.addBlock(block) # Add the current output block to the rung
                block = Block() # Create a new block
                block.addLine("ORLD") # This is used to artifically add an ORLD block
                rung.addBlock(block)
                block = Block()
            elif checkMultipleOutputs(rung_text) and not OUTPUT_BLOCK:
                # print(2)
                if len(block.logic) > 0:
                    rung.addBlock(block) # Add the current output block to the rung
                block = Block() # Create a new block
                block.addLine(line)
                rung.addBlock(block) # Add the current output block to the rung
                block = Block() # Create a new block
                OUTPUT_BLOCK = True
            # Output block is active but previous instruction was "AND" 
            elif len(block.logic) > 0 and OUTPUT_BLOCK and (prev_instr == "AND" and prev_instr == "ANDNOT"):
                # print(3)
                # rung.addBlock(block) # Add the old block to the rung
                # block = Block() # Create a new block
                block.addLine(line)
                rung.addBlock(block) # Add the current output block to the rung
                block = Block() # Create a new block
                # if next_line == None:
                    # print(3.5)
                block = Block() # Create a new block
                block.addLine("ORLD") # This is used to artifically add an ORLD block
                    # rung.addBlock(block)
                    # OUTPUT_BLOCK = False
            elif OUTPUT_BLOCK:
                # print(4)
                block.addLine(line)
                if len(block.logic) > 0:
                    rung.addBlock(block) # Add the current output block to the rung
                block = Block() # Create a new block
                block.addLine("ORLD") # This is used to artifically add an ORLD block
                rung.addBlock(block)
                block = Block()
                if next_line == None:
                    # print(4.5)
                    # block = Block() # Create a new block
                    # block.addLine("ORLD") # This is used to artifically add an ORLD block
                    # rung.addBlock(block)
                    OUTPUT_BLOCK = False
            else:
                # print(5)
                block.addLine(line)
                rung.addBlock(block) # Add the current output block to the rung
                block = Block() # Create a new block

        else:
            # print(6)
            block.addLine(line) # Add any non-specific lines to the block

        if index == len(rung_text) - 1:
            # Append the last block to the rung
            if len(block.logic) > 0:
                rung.addBlock(block) # Add the old block to the rung
            # print("End of Rung")
    
    # rung.viewRung()
    return rung, catchErrors

def assembleBlocks(rung: Rung):
    # This function assembles the blocks into a rung
    blocks = rung.converted_blocks.copy()
    # NUM_BRANCHES = 0 # Used to handle TR branch closing

    # If there are any TR branches and break them up
    if rung.has_TR_blocks:
        rung = TRBreaker(blocks, rung)
        # pprint(rung.TR_blocks)
        
        # In reverse order, convert the TR blocks
        converted_TR_blocks = ""
        for index, TR_block in enumerate(reversed(rung.TR_blocks)):
            # print(rung.TR_blocks[TR_block])
            sub_logic_holder = []
            logic_holder = []
            if len(rung.TR_blocks[TR_block]) > 1:
                # Group up sub blocks
                for index, block in enumerate(rung.TR_blocks[TR_block]):
                    logic = subBlockAssembler(block)
                    sub_logic_holder.append(logic)
                    if index > 0:
                        sub_logic_holder.append("ORLD")
                # Add remaining blocks together now
                logic_holder = subBlockAssembler(sub_logic_holder)
                # print(logic_holder)

                # Now replace this back into the next TR block
                if TR_block > 0:
                    # find index of TR block flag
                    # print("check: ", rung.TR_blocks[TR_block-1])
                    check_flag = "TR"+str(TR_block)
                    # print(check_flag)
                    try:
                        TR_index = rung.TR_blocks[TR_block-1].index([check_flag])
                    except:
                        TR_index = 0
                    
                    # Replace flag with grouped logic
                    # print("pre-holder", logic_holder, rung.TR_blocks[TR_block-1][TR_index-1][-1])
                    if rung.TR_blocks[TR_block-1][TR_index-1][-1] == "ANDLD":
                        rung.TR_blocks[TR_block-1][TR_index-1].append(logic_holder)
                    else:
                        rung.TR_blocks[TR_block-1][TR_index-1][-1] += logic_holder
                    # Remove flag
                    rung.TR_blocks[TR_block-1].pop(TR_index)
                    # print(rung.TR_blocks[TR_block-1][0])
                    # try:
                    #     return rung.TR_blocks[index+1].index(value)
                    # except ValueError:
                    #     return -1  # Value not found
            else:
                # On the final (first) TR block, convert the logic set new_rung
                if TR_block == 0:
                    new_rung = subBlockAssembler(rung.TR_blocks[TR_block][0])
                    # print("final: ", new_rung)
                else:
                    new_rung = subBlockAssembler(rung.TR_blocks[TR_block][0])
    else:
        # If there are no TR branches, convert the blocks normally
        new_rung = subBlockAssembler(blocks)
        # print(new_rung)

    # Clean the logic - check for any errors or missed items
    new_rung = logicCleanup(new_rung)
    
    rung.addConvertedLogic(new_rung)
    return rung

# Not working - currently used
def TRBreaker(blocks, rung: Rung):
    # This function breaks up the TR branches in the rung
    TR_flag = 0
    temp_array = []
    for index, block in enumerate(blocks):
        # print(block)
        if block.find("STBR") != -1:
            # Add to TR Blocks
            temp_flag = int(block.split("-")[1])+1
            # print(TR_flag, temp_flag)
            if temp_flag > TR_flag:
                # print("Inception block")
                if TR_flag in rung.TR_blocks: 
                    rung.TR_blocks[TR_flag].append(temp_array)
                    rung.TR_blocks[TR_flag].append(["TR"+str(temp_flag)])
                else: 
                    rung.TR_blocks[TR_flag] = [temp_array]
                    rung.TR_blocks[TR_flag].append(["TR"+str(temp_flag)])
            else:
                if TR_flag in rung.TR_blocks: rung.TR_blocks[TR_flag].append(temp_array)
                else: rung.TR_blocks[TR_flag] = [temp_array]
            temp_array = [] # Reset temp_array

            TR_flag = int(block.split("-")[1])+1
        
        elif block.find("NWBR") != -1:
            # Add to TR Blocks
            if len(temp_array) > 0:
                if TR_flag in rung.TR_blocks: rung.TR_blocks[TR_flag].append(temp_array)
                else: rung.TR_blocks[TR_flag] = [temp_array]
                # rung.TR_blocks[TR_flag].append(["ORLD"]) # Add an ORLD block
                temp_array = [] # Reset temp_array

                TR_flag = int(block.split("-")[1])+1
            else: continue

        else:
            # Add to TR Blocks
            if len(block) > 0:
                temp_array.append(block)

            # If last block in the array, add to TR Blocks
            if index == len(blocks) - 1:
                if len(temp_array) > 0:
                    if TR_flag in rung.TR_blocks: rung.TR_blocks[TR_flag].append(temp_array)
                    else: rung.TR_blocks[TR_flag] = [temp_array]
                else: continue
        # print(rung.TR_blocks)
        
    return rung

def subBlockAssembler(new_rung: Rung):
    # Used as a sub-function to assemble the blocks
    new_block = ""
    index = 0

    while len(new_rung) > 1:
        block = new_rung[index]
        # print(index, block)
        
        if index > 100: # Watchdog break out of infinite loop
            break
        
        # Handle ORLD block
        if block == "ORLD":
            # print(1)
            # print(index, block)
            # print(index-1, new_rung[index-1])
            # print(index-2, new_rung[index-2])

            if len(new_rung) > 2:
                if index >= 2:
                    # print("ORLD Statement: ", new_rung)
                    # print(new_rung[index], new_rung[index-1], new_rung[index-2])
                    new_block = "[" + new_rung[index-2] + "," + new_rung[index-1] + "]"
                    new_rung[index-2] = new_block # Replace the first block with the new block
                    new_rung.pop(index-1) # Remove the third block
                    new_rung.pop(index-1) # Remove the second block
                else:
                    new_rung.pop(index)
                # print(new_block)
                # Reset index
                index = 0
                continue
            else:
                new_rung.pop(index) # Remove the ORLD block
                continue

        
        # Handle ANDLD block
        elif block == "ANDLD":
            # print(2)
            # print(index, block)
            # print(index-1, new_rung[index-1])
            # print(index-2, new_rung[index-2])
            if len(new_rung) > 2:
                if index >= 2:
            
                    new_block = new_rung[index-2] + new_rung[index-1]
                    new_rung[index-2] = new_block # Replace the first block with the new block
                    new_rung.pop(index-1) # Remove the second block
                    new_rung.pop(index-1) # Remove the third block
                else:
                    new_rung.pop(index)
                # print(new_rung)
                # Reset index and continue
                index = 0
                continue
            else:
                new_rung.pop(index) # Remove the ANDLD block
                continue

        # If end of rung, without any ORLD or ANDLD, combine the remaining blocks
        if index == len(new_rung) - 1:
            # print(3)
            new_block = ""
            index = 0
            while len(new_rung) > 1:
                new_rung[index] = new_rung[index] + new_rung[index+1]
                new_rung.pop(index+1)
        
        # print("End Block :", new_rung)
        # Increment index
        index += 1
    
    return new_rung[0]

def convertInstruction(line: str, catchErrors: dict, tagfile: pd.DataFrame, system_name:str):
    # This function converts an instruction from Omron to AB
    # print(line)
    # Pull in global variable for Oneshots
    global one_shot_index

    # Set default values
    ONS_instr = False
    NEEDS_DN_BIT = False

    # instr, param, instr_type, conv_instr, param2, param3 = extractLine(line)
    instr, params, details = ul.expand_instruction(line)
    instr_type = details["type"]
    conv_instr = details["instr"]

    try: param = params[0]
    except: param = None
    try: param2 = params[1]
    except: param2 = None
    try: param3 = params[2]
    except: param3 = None

    if line[0] == "@":
        ONS_instr = True
        line = line[1:]
    # If it's a timer or counter tag, add the .DN bit
    elif param != None and instr.upper() != "RESET" and (param.find("TIM") != -1 or param.find("CNT") != -1): 
        NEEDS_DN_BIT = True
    # If it's a timer instruction, add TIM to the tag
    elif line.find("TIM ") != -1: 
        param = "TIM" + param
    # If it's a counter instruction, add CNT to the tag
    elif line.find("CNT ") != -1: 
        param = "CNT" + param

    # If it's a scaling instruction, extract internal parameters
    elif instr_type.upper() == "SCALING":
        # Create additional required parameters (P1, P2, P3, P4) for scaling
        try: 
            # print(param2)
            p_base = int(param2.split("DM")[1])
            p_prefix = param2.split("DM")[0] + "DM"
            # print(p_base, p_prefix)
            p1 = param2
            p2 = p_prefix + str(p_base + 1)
            p3 = p_prefix + str(p_base + 2)
            p4 = p_prefix + str(p_base + 3)
        except:
            p1 = p2 = p3 = p4 = param2
        # print("Scaling values: " + p1, p2, p3, p4)

    # If it's a PID instruction, extract internal parameters
    elif instr_type.upper() == "PID":
        # Create additional required parameters (P, I, D, Sampling) for PID
        try: 
            # print(param2)
            p_base = int(param2.split("DM")[1])
            p_prefix = param2.split("DM")[0] + "DM"
            # print(p_base, p_prefix)
            SP = param2
            KP = p_prefix + str(p_base + 1)
            KI = p_prefix + str(p_base + 2)
            KD = p_prefix + str(p_base + 3)
            SampRate = p_prefix + str(p_base + 4)
        except:
            SP = KP = KI = KD = SampRate = param2
        # print("PID values: " + SP, KP, KI, KD, SampRate)
    
    # If it's a MOVB instruction, break up designation word into two destination bits
    elif instr_type.upper() == "BTD":
        # Ensure that the destination bit is in the correct format: 4 numbers with leading zeros if needed
        if param2.find("#") != -1: #Check if it's a hardcoded value (e.g. #10) and remove the #
            param2 = param2.replace("#", "")
        # Make sure param2 has 4 digits
        while len(param2) < 4:
            param2 = "0" + param2
        # print(param2)
        dest_bit = str(int(param2[0:2]))
        source_bit = str(int(param2[2:4]))
        # print(source_bit, dest_bit)


    # Convert the tagname
    if param != None:
        param = convertTagname(param, tagfile, system_name)
    if param2 != None:
        param2 = convertTagname(param2, tagfile, system_name)
    if param3 != None:
        param3 = convertTagname(param3, tagfile, system_name)

    # Check to add .DN bit
    if NEEDS_DN_BIT:
        param = param + ".DN"

    if conv_instr == None or param == None:
        # If instruction has code (xx), remove it using regex
        instr = instr.split("(")[0]
        # Check what type of instruction it is, and just created it with the original instruction
        if param == None:
            converted_instruction = instr
        elif param3 != None:
            converted_instruction = instr + "(" + param + "," + param2 + "," + param3 + ")"
        elif param2 != None:
            converted_instruction = instr + "(" + param + "," + param2 + ")"
        else:
            converted_instruction = instr + "(" + param + ")"
        # if not (instr.find("STBR") != -1 or instr.find("NWBR") != -1):
        #     catchErrors["count"] += 1
        #     catchErrors["list"].append(line)
        #     catchErrors["error"] = True

    # For logical instructions with 2 parameters like MOVE
    elif instr_type.upper() == "LOGICAL": 
        if param.find("#") != -1: #Check if it's a hardcoded value (e.g. #10) and remove the #
            param = param.replace("#", "")
        converted_instruction = conv_instr + "(" + param + "," + param2 + ")"
    # For word copy instructions like XFER (->COP)
    elif instr_type.upper() == "COPY":
        if param.find("#") != -1: #Check if it's a hardcoded value (e.g. #10) and remove the #
            param = param.replace("#", "")
            # Omron arguments are Length, Source, Destination
            # AB arguments are Source, Destination, Length
            converted_instruction = conv_instr + "(" + param2 + "," + param3 + "," + param + ")"
    
    # For BTD instructions like MOVB
    elif instr_type.upper() == "BTD":
        # Omron arguments are Source, Bit Designation, Destination
        # AB arguments are Source, Source Bit, Destination, Destination Bit, Length
        converted_instruction = conv_instr + "(" + param + "," + source_bit + "," + param3 + "," + dest_bit + "," + "1" + ")"

    # For output intsructions like OUT, SET, RSET
    elif instr_type.upper() == "OUTPUT": 
        converted_instruction = conv_instr + "(" + param + ")"
    # For math instructions like ADD, SUB, MUL, SCL
    elif instr_type.upper() == "MATH": 
        #Check if it's a hardcoded value (e.g. #10) and remove the #
        if param.find("#") != -1: param = param.replace("#", "")
        else: param = param
        if param2.find("#") != -1: param2 = param2.replace("#", "")
        else: param2 = param2
        converted_instruction = conv_instr + "(" + param + "," + param2 + "," + param3 + ")"

    # For scaling instructions like SCL, needs to be handled specially
    elif instr_type.upper() == "SCALING":

        # Parameters calculated higher up, before tagname conversion
        # Converted equation is: Result = P3 - (P3 - P1) / (P4 - P2) * (P4 - Input)
        converted_instruction = f"{conv_instr}({param3},{p3}-({p3}-{p1})/({p4}-{p2})*({p4}-{param}))"
        # print(converted_instruction)

    # For PID instructions like PID, needs to be handled specially
    elif instr_type.upper() == "PID":

        # Parameters calculated higher up, before tagname conversion
        # Order of arguments for Omron is Process Variable, Constants (incl. P, I, D, Sampling Period), Control Variable
        # Order of arguments for AB is PID, Process Variable, Tieback(0), Control Variable, Inhold bit (0), Inhold value (0)
        converted_instruction = f"{conv_instr}({param}_PID, {param}, 0, {param3}, 0, 0)"
        # print(converted_instruction)

    elif instr_type.upper() == "ONESHOT":
        converted_instruction = conv_instr + "(" + param + "_storage" + "," + param + ")"

    elif instr_type.upper() == "TIMER":
        if param2.find("#") != -1: #Check if it's a hardcoded value (e.g. #10) and remove the #
            # Convert from 1/10th sec to ms
            preset = str(int(int(param2.replace("#", "")) * 1000 / 10)) 
        else:
            preset = param2
        converted_instruction = conv_instr + "(" + param + "," + preset + "," + "0" + ")"

    elif instr_type.upper() == "COUNTER":
        if param2.find("#") != -1: #Check if it's a hardcoded value (e.g. #10) and remove the #
            preset = param2.replace("#", "")
        else:
            preset = param2
        converted_instruction = "ONS" + "(OneShots[" + str(one_shot_index) + "])" 
        # Make sure to increment global one shot index
        one_shot_index += 1
        converted_instruction += conv_instr + "(" + param + "," + preset + "," + "0" + ")"

    elif instr_type.upper() == "RESET":
        converted_instruction = conv_instr + "(" + param + ")"
    elif instr_type.upper() == "COMPARE":
        if param2.find("#") != -1: #Check if it's a hardcoded value (e.g. #10) and remove the #
            param2 = param2.replace("#", "")
        else:
            param2 = param2
        converted_instruction = conv_instr + "(" + param + "," + param2 + ")"
    elif instr_type.upper() == "KEEP":
        # print("Keep instruction")
        # print(line)
        converted_instruction = conv_instr + "(" + param + ")"

    else:
        # If instruction has code (xx), remove it using regex
        conv_instr = conv_instr.split("(")[0]
        
        # Remove any odd characters from parameter
        param = param.replace("#", "")

        # Build instruction based on which parameters are available
        converted_instruction = conv_instr + "("
        if param != None:
            converted_instruction += param
        if param2 != None:
            converted_instruction += "," + param2
        if param3 != None:
            converted_instruction += "," + param3
        converted_instruction += ")"

    if ONS_instr and param != None:
        converted_instruction = "ONS" + "(OneShots[" + str(one_shot_index) + "])" + converted_instruction
        # Make sure to increment global one shot index
        one_shot_index += 1

    return converted_instruction, catchErrors

def logicCleanup(rung:str): 
    # This function cleans up the logic string
    # print("OG:" + rung)

    # Remove any remaining ORLDs or ANDLDs
    cleaned_rung = rung.replace("ORLD","").replace("ANDLD", "")

    # Clean up unnecessary branch brackets ([[[[)
    # We want to look for any instances of "[[" and a corresponding "]," \
    # and replace "[[" with "[" and "]," with ","
    # NOT WORKING SUFFICIENTLY WELL - CURRENTLY DISABLED
    # x_index = 0
    # y_index = len(cleaned_rung)-1
    # while cleaned_rung.find("[[") != -1:
    #     if cleaned_rung[x_index] == "[" and cleaned_rung[x_index+1] == "[":
    #         for y_index in range(len(cleaned_rung)-1, 0, -1):
    #             if cleaned_rung[y_index]  == "," and cleaned_rung[y_index-1] == "]":
    #                 print("i: ", x_index, cleaned_rung[x_index], cleaned_rung[x_index+1])
    #                 print("y: ", y_index, cleaned_rung[y_index-1], cleaned_rung[y_index])
    #                 cleaned_rung = cleaned_rung[:y_index-1] + cleaned_rung[y_index:]
    #                 y_index = len(cleaned_rung)-1 # Reset index
    #                 cleaned_rung = cleaned_rung[:x_index] + cleaned_rung[x_index+1:]
    #                 x_index = 0 # Reset index
    #                 break
    #     x_index += 1
    #     y_index -= 1
    #     # Watchdog
    #     if x_index > 10000 or y_index < 0:
    #         print("x: ", x_index, "y: ", y_index)
    #         print("Watchdog break")
    #         break

    # print("Cl:" + cleaned_rung)

    return cleaned_rung

def extractLine(line: str):
    # This function extracts the instruction, parameter, param type and converted instruction from an inputted line
    line = line.replace("@" , "")
    args = line.split(" ")
    instr = args[0]
    try: param = args[1]
    except: param = None
    try: param2 = args[2]
    except: param2 = None
    try: param3 = args[3]
    except: param3 = None

    try:
        instr_type = lk.lookup[instr][0]
        conv_instr = lk.lookup[instr][1]
    except:
        instr_type = "None"
        conv_instr = None
    # print(instr, param, param2, param3)

    return instr, param, instr_type, conv_instr, param2, param3


def convertTagname(address: str, tagfile: pd.DataFrame, system_name:str):
    # This function searches the tagfile to determine if a converted tagname exists
    # If it does, it returns the converted tagname
    # If it doesn't, it returns the original tagname
    # print(address)
    INDIRECT_ADDRESS = False

    if tagfile is None:
        return address
    
    # If it's an indirect address, so flag it to be put in the global array
    if address.find("*") != -1:
        address = address.replace("*", "")
        INDIRECT_ADDRESS = True

    # if it's a hardcoded value (e.g. #10), return the value as is
    if address.find("#") != -1:
        return address
    else:
        # Search the tagfile for the address
        # try:
        if address.find("HR") >= 0 or address.find("AR") >= 0:
            query = tagfile.query(f'address == "{address}"')
        elif address.isnumeric() or address.find(".") >= 0:
            # print(1)
            query = tagfile.query(f'address == "{address}"')
        else:
            # print(2)
            query = tagfile.query(f'address == "{address}"')
        # print(query)
        if query.empty:
            converted_tagname = ""
            split = address.split(".")
            tagname = system_name + "_ADDR_"
            for word in split:
                if word == split[-1]: converted_tagname += word
                else: converted_tagname = tagname + word + "_"
        else:
            converted_tagname = query["tagname"].to_string(index=False)
        
        # Add converted tagname to the global array if needed
        if INDIRECT_ADDRESS:
            converted_tagname = "Global_Array[" + converted_tagname + "]" 
            INDIRECT_ADDRESS = False

        # print(converted_tagname)
        return converted_tagname
    
def checkMultipleOutputs(rung):
    # This function checks for multiple outputs in a rung
    # print("Checking for multiple outputs")
    output_count = 0
    for line in rung:
        instr, param, instr_type, conv_instr,_,_ = extractLine(line)
        if instr_type.upper() == "OUTPUT" or instr_type.upper() == "ONESHOT" or instr_type.upper() == "TIMER"\
            or instr_type.upper() == "MATH" or instr_type.upper() == "LOGICAL":
            output_count += 1
        elif instr_type.upper() == "COUNTER":
            output_count += 2
    # print("Num of output: ", output_count) #, ". With: ", rung)
    return (output_count>1)

def findLastLD(rung: Rung):
    # This function finds the last LD index in a block
    return_index = -1
    for index, block in enumerate(rung.blocks):
        # print(block)
        for line in block.logic:
            instr, param, instr_type, conv_instr,_,_ = extractLine(line)
            # print(instr)
            if instr == "LD" or instr == "LDNOT":
                return_index = index
    # print(return_index)
    return return_index


#region DEPRECATED / NOT USED CODE
# NOT USED 
def decodeRung(rung: str):
    # Decode the rung and call the convert function
    converted_rung = ""
    prev_logic = ""
    prev_instr = ""
    # Split instructions into an array; exclude the last empty string
    rung = rung.split(NL)[:-1]

    # Loop through each instruction in the rung
    for index, line in enumerate(rung):
        
        # Split out the instruction and the tag
        args = line.split(" ")

        # Convert the logic from Omron to AB, taking into consideration the last instruction
        logic, prev_logic, conv_instr, prev_instr = convertLogic(args, prev_logic, prev_instr)
        
        # If this is the first instruction, set the logic to prev_logic, but don't add to the rung
        if index == 0:
            prev_logic = logic
            continue
        
        # If this is the last line, add the previous logic and current logic
        if index == len(rung) - 1:
            converted_rung += prev_logic + logic

        # Otherwise, add the previous logic to the rung, and current logic to the previous logic
        else:
            converted_rung += prev_logic
            prev_logic = logic

    # print(converted_rung)
    return converted_rung

# NOT USED
def assembleBlocks_old(rung: Rung):
    # This function assembles the blocks in a rung
    converted_rung = ""
    OR_BLOCK = False
    OUTPUT_BLOCK = False
    for index, block in enumerate(rung.converted_blocks):
        # print(block)
        # Check next block
        try: next_block = rung.converted_blocks[index+1]
        except: next_block = None
        # Check which connector is used
        try: connector = rung.connectors[index]
        except: connector = None
        # Check the next connector
        try: next_connector = rung.connectors[index+1]
        except: next_connector = None
        
        # Check for all possible connectors
        # AND/OR BLOCK HANDLING
        if not OR_BLOCK and next_connector == "ORLD": # This is ahead of the "Start" block to catch the first ORLD
            # print("ORLD Block")
            converted_rung += "[" + block
            OR_BLOCK = True
        elif connector == "START":
            # print("Start Block")
            converted_rung += block
        elif connector == "ANDLD":
            # print("ANDLD Block")
            converted_rung += block
        elif OR_BLOCK and next_connector != "ORLD":
            converted_rung += "," + block + "]"
            OR_BLOCK = False
        elif OR_BLOCK and next_connector == "ORLD":
            converted_rung += "," + block     
        # OUTPUT HANDLING
        elif connector == "OUTPUT" and next_connector != "OUTPUT":
            # print("Output Block")
            converted_rung += block
        elif connector == "OUTPUT" and next_connector == "OUTPUT":
            # print("Output Block")
            converted_rung += "[" + block
            OUTPUT_BLOCK = True
        elif OUTPUT_BLOCK and next_connector == "OUTPUT":
            # print("Output Block")
            converted_rung += "," + block
        elif OUTPUT_BLOCK and next_connector == None:
            # print("Output Block")
            converted_rung += "," + block + "]"
            OUTPUT_BLOCK = False
        elif connector == None:
            pass
        else:
            pass

    
    # print(converted_rung)

# NOT USED 
def convertLogic(line, prev_line, prev_instr):
    # Convert Specific instructions from Omron to AB
    # print(line)
    logic = ""
    instr = line[0]
    instr_type = lk.lookup[instr][0]
    try:
        prev_instr_type = lk.lookup[prev_instr][0]
    except: prev_instr_type = None

    # print(prev_instr_type, instr_type)
    # Previous Line Modifications
    if prev_instr_type == "OR" and instr_type == "AND":
        logic += "]"

    # Handle various instructions
    if instr == "ORLD":
        logic += "" # Hold off handling for now
    elif instr == "ANDLD":
        conv_instr = lk.lookup[instr][1]
        logic += conv_instr
    elif instr == "":
        logic += "" # Placeholder for other complicated instructions
    else:
        param = line[1]
        conv_instr = lk.lookup[instr][1]
        logic += conv_instr + "(" + param + ")"

    # Handle last line updates
    if instr == "OR" or instr == "ORNOT":
        if prev_instr == "OR":
            prev_logic = prev_line
        else:
            prev_logic = "[" + prev_line
    else: 
        prev_logic = prev_line
    # print(logic)
    prev_instr = instr
    return logic, instr, prev_logic, conv_instr, prev_instr
#endregion

