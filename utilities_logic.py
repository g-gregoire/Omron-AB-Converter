import lookup as lk
from structures import Block, Rung

from typing import List, Dict
import re
import pandas as pd
import copy

TEST_TAG = "D32253"

def expand_instruction(line: str):
    # This function expands the instruction into its instruction, parameters and details
    # Returned values look like: "MOV(21)", ["A", "B"], {"instr": "MOV", "type": "copy", "args": 2, "block_type": "OUT", "blocks_in": 1}
    if line.find("@") != -1 or line.find("!") != -1 or line.find("%") != -1:
        # print("ONS instruction found")
        ONS_instr = True
        ONS_type = line[0]
        line_strip = line.replace("@" , "").replace("!","").replace("%","")
    else:
        ONS_instr = False
        ONS_type = ""
        line_strip = line
    args = line_strip.split(" ")
    instr = args[0].replace("(0","(") # Remove leading 0 from instruction code if it exists (ie. MOV(021) -> MOV(21))
    params = args[1:]

    # Get instruction into from lookup table
    try:
        details = lk.lookup[instr]
        details["logic"] = line
    except:
        details = None

    instr_final = ONS_type + instr

    return instr_final, params, details, ONS_instr, ONS_type

def combine_compare(rung:Rung, rung_array:List[str], index:int, current_details, catchErrors):
    # print("Compare")
    pop_array = [index] # We already know we need to pop this index

    line1 = rung_array[index]
    line2 = rung_array[index + 1] if index + 1 < len(rung_array) else None
    line3 = rung_array[index + 2] if index + 2 < len(rung_array) else None
    line4 = rung_array[index + 3] if index + 3 < len(rung_array) else None
    # print("Line 1: ", line1)
    # print("Line 2: ", line2)
    # print("Line 3: ", line3)
    # print("Line 4: ", line4)
    # Determine which comparison is being used
    EQU = GRT = LES = False
    if line2.find("LD TR") != -1 or line2.find("OUT TR") != -1:
        check1 = line3
        check1_index = index + 2
        check2 = line4
        check2_index = index + 3
    else:
        check1 = line2
        check1_index = index + 1
        check2 = line3
        check2_index = index + 2
    if check1 == None or check1 == "": # Added for strange coding where CMP and comp_type are on different rungs
        print("Incorrect usage of CMP instruction")
        catchErrors["count"] += 1
        catchErrors["list"].append(line1)
        rung.comment += f" - ERROR with ({line1})- NO FOLLOW-UP COMPARISON ARGS (GRT, LEQ, etc.)."
    else:
        if check1.find("EQUALS") != -1 or check1.find("P_EQ") != -1:
            EQU = True
            pop_array.append(check1_index)
        elif check1.find("GREATER_THAN") != -1 or check1.find("P_GT") != -1 or check1.find("GE") != -1:
            GRT = True
            pop_array.append(check1_index)
        elif check1.find("LESS_THAN") != -1 or check1.find("P_LT") != -1 or check1.find("LE") != -1:
            LES = True
            pop_array.append(check1_index)
        if check2.find("EQUALS") != -1 or check2.find("P_EQ") != -1:
            EQU = True
            pop_array.append(check2_index)
        elif check2.find("GREATER_THAN") != -1 or check2.find("P_GT") != -1 or check2.find("GE") != -1:
            GRT = True
            pop_array.append(check2_index)
        elif check2.find("LESS_THAN") != -1 or check2.find("P_LT") != -1 or check2.find("LE") != -1:
            LES = True
            pop_array.append(check2_index)
        # print(EQU, GRT, LES)
    
        if EQU and GRT:
            # print("GEQ")
            line1 = line1.replace("CMP(20)", "GEQ").replace("CMP(020)", "GEQ").replace("CMPL(060)", "GEQ")
        elif EQU and LES:
            # print("LEQ")
            line1 = line1.replace("CMP(20)", "LEQ").replace("CMP(020)", "LEQ").replace("CMPL(060)", "LEQ")
        elif EQU:
            # print("EQU")
            line1 = line1.replace("CMP(20)", "EQU").replace("CMP(020)", "EQU").replace("CMPL(060)", "EQU")
        elif GRT:
            # print("GRT")
            line1 = line1.replace("CMP(20)", "GRT").replace("CMP(020)", "GRT").replace("CMPL(060)", "GRT")
        elif LES:
            # print("LES")
            line1 = line1.replace("CMP(20)", "LES").replace("CMP(020)", "LES").replace("CMPL(060)", "LES")
        else:
            line1 = line1.replace("CMP(20)", "LES").replace("CMP(020)", "LES").replace("CMPL(060)", "LES")

        # Next, check if double compare, if the next line is an ANDLD
        if len(pop_array) == 3:
            # print("Double compare found")
            ANDLD_index = pop_array[-1]
            # print(rung_array[ANDLD_index+1])
            if rung_array[ANDLD_index+1].find("ANDLD") != -1:
                # print("Trailing ANDLD found", rung_array[ANDLD_index+1])
                pop_array.append(ANDLD_index+1)

        print("Pop array: ", pop_array)

        # Lastly deal with TR block, if it exists
        if line2.find("LD TR") != -1 or line2.find("OUT TR") != -1:
            instr, params, details,ONS_instr,_ = expand_instruction(line2)
            instr_type = details["type"]
            details_add = details.copy() # Need to create copy due to dictionary reference

            if instr == "OUT":
                details_add["logic"] = f"START({params[0]})"
                block_type = details_add["block_type"] = "TR"
                details_add["type"] = "START"
            else:
                details_add["logic"] = f"OUT({params[0]})"
                block_type = details_add["block_type"] = "TR"
                details_add["type"] = "OUT"
            current_details, type_array = rung.addBlock(Block([details_add], block_type, details_add["blocks_in"]))
    
        # print(line1, pop_count)
    return line1, pop_array, current_details, catchErrors

def combine_simple_logic(block_array:List[Block])->List[Block]:
    # print("New combine")
    index = 0
    multiple_out_added = 0
    working_logic = []
    type_array = []
    OR_active = False

    multiple_count = 0
    for block in block_array:
        if block.block_type == "OUT":
            multiple_count += 1
    if multiple_count > 1:
        multiple_OUT = True
        # print("Multiple OUT blocks:", multiple_count)
    else:
        multiple_OUT = False

    for index, block in enumerate(reversed(block_array)):

        if block.details[0]["block_type"] == "TR":
            working_logic.append(block.details[0]["logic"])
            continue
        
        # Get working variables
        logic = block.converted_block
        block_type = block.block_type
        type_array.append(block_type) # Append block type for type determination later
        # print(index, block, block_type)

        # Determine previous block in array (next one in reversed array)
        try:
            prev_block = block_array[-index-2]
        except:
            prev_block = None

        if block_type == "OUT":
            # print("OUT type. Line: ", logic)
            if multiple_OUT: # If multiple outputs, we need brackets for branches
                if logic[0][0] == "[" and logic[0][-1] == "]":
                    # print("Brackets. Before", logic[0], "After", logic[0][1:-1])
                    logic[0] = logic[0][1:-1]
                    # print("logic: ", logic)
                if multiple_out_added == 0:
                    working_logic.append("]")
                    working_logic.append(logic[0])
                    multiple_out_added += 1
                    # print("set OR active")
                    OR_active = True
                elif 0 < multiple_out_added < (multiple_count - 1):
                    working_logic.append(",")
                    working_logic.append(logic[0])
                    multiple_out_added += 1
                elif multiple_out_added == multiple_count - 1:
                    working_logic.append(",")
                    working_logic.append(logic[0])
                    working_logic.append("[")
                    OR_active = False
                else:
                    working_logic.append(logic[0])
            else: # If single output, no brackets needed
                working_logic.append(logic[0])

        elif block_type == "START" or block_type == "IN": # If start (LD) or IN block, then close bracket is it's open
            if multiple_OUT: # If multiple outputs, we need brackets for branches
                # if 0 < multiple_out_added <= multiple_count:
                #     working_logic.append(logic[0])
                # elif multiple_out_added == multiple_count:
                #     working_logic.append("[")
                #     working_logic.append(logic[0])
                # else:
                if OR_active and (multiple_out_added > 1): # If or active, and more than 1 output added already, wrap output in brackets
                    # print("OR active - wrap in brackets")
                    working_logic.insert(0, "]")
                    working_logic.append("[")
                    working_logic.append(logic[0])
                else:
                    working_logic.append(logic[0])
            else: # If single output, no brackets needed
                working_logic.append(logic[0])

        # print(working_logic)
    output_logic = "".join(reversed(working_logic))

    # print(output_logic)
    combined_type = determine_block_type(type_array)
    # print("Combined type: ", combined_type)
    details = {
        "logic": output_logic,
        "block_type": combined_type,
        "blocks_in": 1
    }
    block_type = combined_type
    blocks_in = 1

    output_block = [Block([details], block_type, blocks_in)]

    return output_block

def combine_block_list(block_array:List[Block], catchErrors)->List[Block]:
    # This function takes a list of blocks and combines them into a single OR block
    # This is done by adding brackets around each block and adding a comma between each block
    # The output is a single block with the logic of all blocks combined
    # print("OR block list")
    # for index, block in enumerate(block_array):
    #     print(index, block)

    working_logic = []
    type_array = []
    for index, block in enumerate(reversed(block_array)):
        logic = block.converted_block
        block_type = block.block_type
        type_array.append(block_type) # Append block type for type determination later

        # Check next block in rev array (prev one in actual array)
        prev_block = block_array[-index-2] if index < len(block_array) - 1 else None
        prev_block_type = prev_block.block_type if prev_block else None
        
        if len(logic) == 0:
            print("Logic is None")
            catchErrors["error"] = True
            continue
        # print("Block", index, logic, block_type)
        # print("Prev block", prev_block)

        if index == 0:
            working_logic.append("]")
        
        # Append actual logic
        working_logic.append(logic[0])

        if prev_block_type != None and (prev_block_type == "START" or prev_block_type == "IN") or index == len(block_array) - 1:
            pass
        else:
            working_logic.append(",")
    working_logic.append("[")
        
    output_logic = "".join(reversed(working_logic))
    combined_type = determine_block_type(type_array)
    details = {
        "logic": output_logic,
        "block_type": combined_type,
        "blocks_in": 1
    }
    block_type = combined_type
    blocks_in = 1
    output_block = [Block([details], block_type, blocks_in)]
    
    return output_block, catchErrors

def createSubSet(block_list:List[Block], start_index:int, end_index:int) -> List[Block]:
        # print("Creating subset. Indexes: ", start_index, end_index)
        # for block in block_list:
        #     print(block)
        # Create new block list with copies of the blocks in the range
        temp_subset = block_list[start_index:end_index]
        subset = copy.deepcopy(temp_subset)
        # print("Subset. Indexes: ", start_index, end_index)
        # for block in subset:
        #     print(block)
        return subset

def concat_block_list(initial:List[Block], inter:List[Block], final:List[Block]) -> List[Block]:
    block_list = []

    if initial != None:
        for block in initial:
            block_list.append(block)
    block_list.append(inter[0])
    if final != None:
        for block in final:
            block_list.append(block)

    # print("Concatenated block list")
    # for block in block_list:
    #     print(block)
    return block_list

def determine_block_type(type_array:List[str]) -> str:
    if len(type_array) == 1:
        block_type = type_array[0]
    else:
        if "START" in type_array:
            block_type = "START"
        elif "OUT" in type_array:
            block_type = "OUT"
        else:
            block_type = "IN"
    return block_type