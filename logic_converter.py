import file_functions as ff
import lookup as lk
import utilities_logic as ul
import utilities as util
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
        if rowindex == logic_file.index[-1]:
            end_of_rung = True
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

def loop_rungs_v2(output_file, simple_output, routine: Routine, tagfile: pd.DataFrame, system_name:str, view_rungs = False, start_rung=0, num_rungs=-1):
    # This function converts the rungs in a routine
    rung_num = 0
    catchErrors = {
        "count": 0,
        "list": [],
        "error": False
    }
    for index, rung in enumerate(routine.rungs):
        # print("\nRung", rung_num)
        # print("Original", rung.original)
        rung.num = rung_num

        if rung.original == "": # Handle empty rung
            print("Empty rung")
            rung.converted_logic = "NOP()"
        elif rung.original.find("END(001)") != -1: # Handle end of program
            print("End of routine")
            rung.converted_logic = "NOP()"
            rung.comment = "End of Routine."
        else:
            rung, catchErrors = block_breaker_v2(rung, catchErrors)
            # rung.viewBlocks(f" Rung {rung.num}. After block breaker")
            rung, catchErrors = convert_blocks(rung, catchErrors, tagfile, system_name)
            # rung.viewBlocks("After block conversion")
            rung, catchErrors = block_assembler_v2(rung, catchErrors)
            # rung.viewBlocks("After block assembler")

        # Add the rung to the output file
        rung_num = ff.addRung(output_file, simple_output, rung_num, rung.converted_logic, rung.comment)
        # rung_num += 1

        # If the view_rungs flag is set, print the rung
        if view_rungs:
            rung.viewBlocks()

        # If the number of rungs is not specified, continue to the end of the file
        if num_rungs == -1:
            pass
        # If the number of rungs is specified, check if the number of rungs is reached
        elif rung_num >= (start_rung+num_rungs):
            routine.rungs[index] = rung # Update the rung in the routine object
            print("Reached end of requested rungs")
            return routine, catchErrors
            
        routine.rungs[index] = rung # Update the rung in the routine object
        
    return routine, catchErrors

def block_breaker_v2(rung: Rung, catchErrors: dict):
    # This function splits rung into logic/load blocks
    # Initialize variables
    rung_text = rung.original
    rung_array = rung_text.split(NL)[:-1]
    current_details = []
    current_block_type = ""
    type_array = []
    blocks_in = 1
    DEBUG_bbv2 = False

    # for index, line in enumerate(rung_array):
    #     print(index, line)

    # Loop through each instruction in the rung_text
    index = 0
    # for index, line in enumerate(rung_array):
    while index < len(rung_array):
        line = rung_array[index]
        instr, params, details,ONS_instr,_ = ul.expand_instruction(line)
        # print(index, ONS_instr, line, instr, params, details)
        if DEBUG_bbv2: print(index, details)
        block_type = details["block_type"]
        instr_type = details["type"]
        details_add = details.copy() # Need to create copy due to dictionary reference

        if re.search(r"TR[\d]", line): # Search for TR blocks, between TR0 and TR15
            if current_details != []:
                add_type = ul.determine_block_type(type_array)
                current_details, type_array = rung.addBlock(Block(current_details, add_type, blocks_in))

            # print("TR block: ", details_add)
            if instr == "OUT":
                details_add["logic"] = f"START({params[0]})"
                block_type = details_add["block_type"] = "TR"
                details_add["type"] = "START"
            elif instr == "LD":
                details_add["logic"] = f"OUT({params[0]})"
                block_type = details_add["block_type"] = "TR"
                details_add["type"] = "OUT"
            current_details, type_array = rung.addBlock(Block([details_add], block_type, details_add["blocks_in"]))

        elif block_type == "INTER" and current_details != []: # ANDLD or ORLD, with a current block
            if DEBUG_bbv2: print("-", 1, current_details)
            # Log the current block before continuing
            add_type = ul.determine_block_type(type_array)
            current_details, type_array = rung.addBlock(Block(current_details, add_type, blocks_in))
            
            # Continue and immediately log ANDLD/ORLD block
            current_details, type_array = rung.addBlock(Block([details_add], block_type, details_add["blocks_in"]))
            
            
        elif block_type == "INTER" and current_details == []: # ANDLD or ORLD, with no current block (ie back-to-back ANDLD/ORLD)
            if DEBUG_bbv2: print("-", 1, current_details)
            # Continue and immediately log ANDLD/ORLD block
            current_details, type_array = rung.addBlock(Block([details_add], block_type, details_add["blocks_in"]))
            

        elif block_type == "START" and current_details == []: # LD-type instruction and no current block
            current_details.append(details_add)
            type_array.append(block_type)
            if DEBUG_bbv2: print("-", 2, current_details)

        elif block_type == "START" and current_details != []: # LD-type instruction with an existing block
            if DEBUG_bbv2: print("-", 3, current_details)
            # Log the current block before continuing
            add_type = ul.determine_block_type(type_array)
            current_details, type_array = rung.addBlock(Block(current_details, add_type, blocks_in))
            
            # Continue
            current_details.append(details_add)
            type_array.append(block_type)

        elif instr_type.upper() == "COMPARE_OLD":
            # Add the current block to the rung before continuing. This is needed due to output style of old compare blocks
            if current_details != []:
                add_type = ul.determine_block_type(type_array)
                current_details, type_array = rung.addBlock(Block(current_details, add_type, blocks_in))

            try: next_line = rung_array[index + 1]
            except: next_line = None
            try: after_next_line = rung_array[index + 2]
            except: after_next_line = None
            combined_instr, pop_array, current_details, catchErrors = ul.combine_compare(rung, rung_array, index, current_details, catchErrors)
            # print(catchErrors)

            if DEBUG_bbv2: print("Combined: ", combined_instr)
            details_add["logic"] = combined_instr
            current_details.append(details_add)

            # Pop required lines
            # print(rung_array)
            # print(rung_array[index])
            for i in reversed(pop_array):
                # print("Popping: ", rung_array[i])
                rung_array.pop(i)

            index -= 1 # Decrement index since we popped a line
            # print(rung_array)
            

        elif block_type == "OUT" and current_details == []: # Output-type instruction and no current block
            if DEBUG_bbv2: print("-", 4, current_details)
            # Immediately log output block
            current_details, type_array = rung.addBlock(Block([details_add], block_type, details["blocks_in"]))
            

        elif block_type == "OUT" and current_details != []: # Output-type instruction with an existing block
            if DEBUG_bbv2: print("-", 5, current_details)
            # Log the current block before continuing
            add_type = ul.determine_block_type(type_array)
            current_details, type_array = rung.addBlock(Block(current_details, add_type, blocks_in))
            
            # Continue and immediately log output block
            current_details, type_array = rung.addBlock(Block([details_add], block_type, details["blocks_in"]))
            
            
        elif block_type == "IN" or block_type == "OR": # Standard instruction
            current_details.append(details_add)
            type_array.append(block_type)
            blocks_in = details["blocks_in"]
            if DEBUG_bbv2: print("-", 6, current_details)

        elif block_type == "NOP": # No instruction
            current_details.append(details_add)
            type_array.append(block_type)
            blocks_in = details["blocks_in"]
            if DEBUG_bbv2: print("-", 7, current_details)

        # Catch the last block
        if index == len(rung_array) - 1 and current_details != []:
            if DEBUG_bbv2: print("-", 8, current_details)
            add_type = ul.determine_block_type(type_array)
            current_details, type_array = rung.addBlock(Block(current_details, add_type, blocks_in))

        index += 1
            
        
    return rung, catchErrors

def convert_blocks(rung: Rung, catchErrors: dict, tagfile: pd.DataFrame, system_name:str):
    # This function converts the blocks in a rung
    for index, block in enumerate(rung.blocks):
        # print("Block:", block)

        if block.block_type == "TR" or block.block_type == "INTER":
            # print("Skip TR block conversion")
            continue

        # Loop through each instruction in the block
        for index, line in enumerate(block.converted_block):
            # print("Line:", line)
            instr, params, details,ONS_instr,_ = ul.expand_instruction(line)
            # print(ONS_instr, line, instr, params, details)


            # Convert the instruction
            converted_instruction, catchErrors = convert_instruction(line, catchErrors, tagfile, system_name)
            if catchErrors["error"]: 
                catchErrors["count"] += 1
                rung.comment += f" - ERROR CONVERTING THIS RUNG ({instr})."
                if "message" in catchErrors:
                    rung.comment += f" {catchErrors['message']}"
                catchErrors["error"] = False

            # Update the converted_block and details["logic"] with the converted instruction
            block.converted_block[index] = converted_instruction
            block.details[index]["logic"] = converted_instruction
            # print(converted_instruction)

    return rung, catchErrors

def block_assembler_v2(rung: Rung, catchErrors: dict):
    ### This function reassemble the blocks into a rung
    # Steps: 
    # 1. Handle basic inner joins (inside block) (Forward pass)
    # 2. Handle ANDLD and ORLD blocks (Forward pass)
    # 3. Handle special output blocks: CNT, TTIM, KEEP (Reverse pass)
    # 4. Handle normal output-type blocks and remaining joins (Reverse pass)
    # 5. Handle TR x blocks
    ###
    

    # rung.viewBlocks("Initial view")

    # 1. FORWARD PASS - handle basic inner joins
    for index, block in enumerate(rung.blocks):
        # print(block.details)
        if len(block.logic) > 1: # Join simple blocks
            block.innerJoin()
        else: # Single line block -> set to converted_logic
            block.converted_block = block.logic

    # rung.viewBlocks("After inner join pass")

    # 2. FORWARD PASS - handle ANDLD and ORLD blocks
    index = 0
    while index < len(rung.blocks): 
        block = rung.blocks[index]
        next_block = rung.blocks[index + 1] if index + 1 < len(rung.blocks) else None
        prev_block = rung.blocks[index - 1] if index - 1 >= 0 else None
        prev2_block = rung.blocks[index - 2] if index - 2 >= 0 else None
        # print("Prev2 block:", prev2_block)
        # print("Prev block:", prev_block)
        # print("This:", index, block, block.block_type)
        # print("Next block:", next_block)
        
        if block.block_type == "INTER": # For ANDLD and ORLD blocks
            if prev2_block != None and prev2_block.block_type == "TR": # If we come across a TR block, add it to the following block and then perform the join
                pop_index = index-1
                # print("TR block found:", prev_block)
                # print(rung.blocks[index-2])
                # print(rung.blocks[index-3])
                rung.join2Blocks(index-3, index-2, "AND") # Join the TR block to the one before it.
                TR_offset = True
            else:
                pop_index = index
                TR_offset = False

            if block.details[0]["instr"] == "ANDLD":
                rung.blocks.pop(pop_index) # Remove the ANDLD block
                if index == 1: # If it's the first block, then handle differently so we don't append index -1
                    pass
                else:
                    # print("ANDLD")
                    # print(rung.blocks[index-2])
                    # print(rung.blocks[index-3])
                    if TR_offset: # If we have a TR block, then join to the previous 2 blocks
                        rung.join2Blocks(index-3, index-2, "AND") # Join the previous 2 blocks
                        TR_offset = False
                    else:
                        rung.join2Blocks(index-2, index-1, "AND") # Join the previous 2 blocks
                # index = 0 # Reset counter since we popped a block
                # print("End: ", rung.blocks[index-1], NL)
                
            elif block.details[0]["instr"] == "ORLD":
                rung.blocks.pop(pop_index) # Remove the ORLD block
                if index == 1: # If it's the first block, then handle differently so we don't append index -1
                    pass
                else:
                    if TR_offset:
                        rung.join2Blocks(index-3, index-2, "OR")
                        TR_offset = False
                    else:
                        rung.join2Blocks(index-2, index-1, "OR") # Join the previous 2 blocks
                    # index = 0 # Reset counter since we popped a block
                    # print("End: ", rung.blocks[index-1], NL)
                
            # If next block is an IN block, then join to previous block. This is to handle case where a basic IN block needs to be joined to the previous ANDLD'd block
            if next_block != None and next_block.block_type == "IN" or next_block.block_type == "OR": 
                # print("In block found:", next_block)
                # print("Block1:", rung.blocks[index-2].block_type, rung.blocks[index-2])
                # print("Block2:", rung.blocks[index-1].block_type, rung.blocks[index-1])
                if next_block.block_type == "IN":
                    rung.join2Blocks(index-2, index-1, "AND") # Join the previous 2 blocks
                elif next_block.block_type == "OR":
                    rung.join2Blocks(index-2, index-1, "OR")
                # print("End: ", rung.blocks[index-1], NL)

            index = 0 # Reset counter since we popped a block
            continue

        index += 1

    # rung.viewBlocks("After ANDLD/ORLD block pass")

    # 3. REVERSE PASS - handle special output blocks: CNT, TTIM, KEEP
    index = len(rung.blocks) - 1
    while index >= 0: # Could be improved - multiple ORLD creates multiple nested branches
        block = rung.blocks[index]
        block_type = block.block_type
        prev_block = rung.blocks[index-1] if index - 1 >= 0 else None
        prev2_block = rung.blocks[index-2] if index - 2 >= 0 else None
        prev3_block = rung.blocks[index-3] if index - 3 >= 0 else None
        
        # print("1-", index, block)
        # print("2-", block.details[0])
        if block_type == "OUT":
            if "type" in block.details[0] and (block.details[0]["type"].upper() == "COUNTER" or block.details[0]["type"].upper() == "KEEP" or block.details[0]["type"].upper() == "RET_TIMER"):
                # print(index, block, block_type)
                # print(index-1, prev_block)
                # print(index-2, prev2_block)
                # print(index-3, prev3_block)
                # Check if prev2 block is a TR block
                if prev2_block != None and prev2_block.block_type == "TR":
                    # First, join the TR block to the previous block
                    rung.join2Blocks(index-2, index-1, "AND")
                    # Then, join the rest of the blocks
                    # print(rung.blocks[index-1])
                    # print(rung.blocks[index-2])
                    # print(rung.blocks[index-3])
                    rung.join3Blocks(index-3, index-2, index-1, block.details[0]["type"])
                else:
                    rung.join2Blocks(index-2, index-1, block.details[0]["type"])
                index = len(rung.blocks) - 1 # Reset counter since we popped a block
            # elif block.details[0]["type"].upper() == "RET_TIMER":
            #     match = re.search(r"XIC\(\w+\)RES\(\w+\)", block.converted_block[0])
            #     if match:
            #         print("Match: ", match.group(0))
            #         tag = match.group(0)
            #         block.converted_block[0] = block.converted_block[0].replace(tag, "")
            #     else: tag = "???" # Placeholder for error
            #     reset_instruction = "RES(" + tag + ")"

        # rung.viewBlocks()
        index -= 1

    rung.viewBlocks("After special output pass")
    

    # Check if TR blocks exist for next pass. Also find highest TR number
    TR_array = {}
    TR_exists = False
    for block in rung.blocks:
        # print("Block: ", block, block.block_type)
        # Check if block is TR type, or if it contains a Start TR block
        if (block.block_type == "TR" and block.details[0]["type"] == "START") or ("START(TR" in block.converted_block[0]):
            # print("Found block", block)
            TR_number = re.search(r"TR([\d])", block.converted_block[0]).group(1)
            if int(TR_number) in TR_array:
                TR_array[int(TR_number)] += 1
            else:
                TR_array[int(TR_number)] = 1
            # TR_array.sort()

            TR_exists = True
    
    # print("TR exists: ", TR_exists)
    # if TR_exists:
        # print("TR numbers: ", TR_array)

    # 4. REVERSE PASS - handle normal output-type blocks and remaining joins. (Skip if TR blocks exist)
    if not TR_exists: # IF no TR blocks, then we can proceed with normal logic
        
        # Call function to combine logic blocks
        rung.blocks = ul.combine_simple_logic(rung.blocks)
        # rung.viewBlocks("After normal output pass")


    else: # IF TR blocks exist, then we need to handle them with subblocks

        # Run through for each TR# we have
        for num in reversed(TR_array):
            while TR_array[num] > 0:
                print("TR#", num, " - Remaining TR blocks: ", TR_array[num])
                TR_num = "TR" + str(num)
                next_TR_num = "TR" + str(num - 1)
                start_TR_num = "START(" + TR_num + ")"
                out_TR_num = "OUT(" + TR_num + ")"
                print("Now,", TR_num)
                # First create subblocks for TR blocks
                initial = True
                prev_index = 0
                inter_array = []
                initial_subset = []
                final_subset = None
                TR_num_converted = 1
                TR_num_total = TR_array[num]

                for index, block in enumerate(rung.blocks):
                    print(index, block)

                index = 0
                # for index, block in enumerate(rung.blocks):
                while index < len(rung.blocks):
                    block = rung.blocks[index]
                    print("Index: ", index, block.converted_block[0])
                    
                    if initial == False and re.search(next_TR_num, block.converted_block[0]) is not None: # This is used to capture what is after the TR blocks, and will remain untouched (for now)
                        # print("Next block - add inter & final subset")
                        # print("inter", prev_index+1, index)
                        inter_subset = ul.createSubSet(rung.blocks, prev_index+1, index, out_TR_num)
                        inter_array.append(inter_subset)
                        print(index, "Inter append-1")
                        for block in inter_subset: print(block)
                        # print("final", index, len(rung.blocks))
                        if prev_index+1 == index:
                            final_subset = ul.createSubSet(rung.blocks, index+1, len(rung.blocks), out_TR_num)
                        else:
                            final_subset = ul.createSubSet(rung.blocks, index, len(rung.blocks), out_TR_num)
                        # for block in final_subset: print(block)
                        break # Break out since we've found the first of the next TR group

                    elif block.converted_block[0].find(start_TR_num) != -1: # Used to capture if it's the first TR block
                        # print("Start block - add initial subset")
                        
                        if TR_num_converted < TR_num_total: # Used to skip the first TR block if there are multiple
                            TR_num_converted += 1
                            # print("Skip first TR start block")
                            index += 1
                            continue

                        if ("START(TR" in block.converted_block[0]) and block.block_type != "TR": # Used to capture when Start(TR is embedded in a block
                            # print("Start block embedded in block", block.converted_block)
                            # We need to split the block into 2 parts, and add the first part to the initial subset and the second to the inter array
                            temp_blocks = block.converted_block[0].split(start_TR_num) 

                            # First set initial block as everything before TR0
                            initial_subset = ul.createSubSet(rung.blocks, 0, index+1, out_TR_num)
                            initial_subset[-1].converted_block[0] = temp_blocks[0]
                            # for block in initial_subset: print(block)
                            # print("Initial Subset-1")
                            # for block in initial_subset: print(block)
                            
                            # Then set the inter block as everything after TR0
                            inter_subset = ul.createSubSet(rung.blocks, 0, index+1, out_TR_num)
                            inter_subset[-1].converted_block[0] = temp_blocks[1]
                            inter_array.append(inter_subset)
                            print(index, "Inter append-2")
                            for block in inter_subset: print(block)

                        else:
                            initial_subset = ul.createSubSet(rung.blocks, 0, index, out_TR_num)


                        # for block in initial_subset: print(block)
                        prev_index = index
                        initial = False
                    
                    elif block.converted_block[0].find(out_TR_num) != -1: # Find intermediate TR blocks
                        # print("OUT block - add inter subset", block.block_type, block.converted_block[0])
                        if initial:
                            # print("Skip blocks until we add a Start block")
                            index += 1
                            continue
                        if block.block_type != "TR": # To capture if the TR block is embedded in a block
                            print("--OUT block embedded in block", block.converted_block)
                            block.converted_block[0] = block.converted_block[0].replace(out_TR_num, "")
                            print("replaced -",out_TR_num, block.converted_block)

                        # print(prev_index+1, index)
                        # if block.converted_block[0] == out_TR_num:
                        #     print("OUT block only")
                        #     # index += 1
                        #     # continue
                        # else:
                        if index == prev_index+1 and block.converted_block[0] == out_TR_num: # Handle case where the OUT TR0 block is the only block
                            # print("OUT block only")
                            inter_subset = []
                            pass
                        else:
                            print("Subset idx:", prev_index+1, index+1)
                            inter_subset = ul.createSubSet(rung.blocks, prev_index+1, index+1, out_TR_num)

                        if len(inter_subset) > 0:
                            inter_array.append(inter_subset)
                            print(index, "Inter append-3")
                            for block in inter_subset: print(block)
                        prev_index = index
                
                    elif index == len(rung.blocks) - 1: # Used to add last block to the inter-set
                        print("Last block - add inter & final subset")
                        print("Subset idx:", prev_index+1, index)
                        inter_subset = ul.createSubSet(rung.blocks, prev_index+1, index, out_TR_num)
                        inter_array.append(inter_subset)
                        print(index, "Inter append-4")
                        for block in inter_subset: print(block)

                    index += 1
                
                
                # Print all sections - for debugging
                local_debug = True

                if local_debug:
                    print("Initial Subset-end")
                    for block in initial_subset: print(block)
                    print("Inter Array")
                conv_array = []
                for idx, inter in enumerate(inter_array):
                    if local_debug: 
                        print("Subset", idx)
                        for block in inter: print("Inter blocks:", block)
                    converted_block = ul.combine_simple_logic(inter)
                    # print("Converted Block:", converted_block[0])
                    conv_array.append(converted_block[0])
                # print("Converted Array")
                # for block in conv_array: print(block, block.block_type)
                # OR blocks together
                new_inter_block, catchErrors = ul.combine_block_list(conv_array, catchErrors)
                # print("Combined inter Block:", new_inter_block[0])
                if local_debug:
                    if final_subset != None:
                        print("Final Subset")
                        for block in final_subset: print(block)
                        print("End.")

                # Combine the initial, converted-inter and final (if it exists)
                rung.blocks = ul.concat_block_list(initial_subset, new_inter_block, final_subset)
                # print("Rung blocks-end", TR_array[num])
                # for block in rung.blocks: print(block)
                
                # Decrement the TR block count for the while loop
                TR_array[num] -= 1

        
        # Lastly, once we're done with all TR blocks, we can combine the logic blocks
        rung.blocks = ul.combine_simple_logic(rung.blocks)
    
    # Finally, set the converted logic to the correct string property
    rung.converted_logic = rung.blocks[0].converted_block[0]
    if catchErrors["error"]: 
        catchErrors["count"] += 1
        rung.comment += f" - ERROR CONVERTING THIS RUNG - UNEXPECTED LOGIC."
        rung.comment += f" \n Attempted Logic: {rung.converted_logic}"
        rung.converted_logic = "NOP()"
        catchErrors["error"] = False
        # rung.viewBlocks()
    
    return rung, catchErrors

def convert_instruction(line: str, catchErrors: dict, tagfile: pd.DataFrame, system_name:str):
    # This function converts an instruction from Omron to AB
    # print(line)
    # Pull in global variable for Oneshots
    global one_shot_index

    # Set default values
    # ONS_instr = False
    NEEDS_DN_BIT = False

    # instr, param, instr_type, conv_instr, param2, param3 = extractLine(line)
    instr, params, details, ONS_instr, ONS_type = ul.expand_instruction(line)
    # print(ONS_instr, line, instr, params, details)
    # print(instr, details)

    instr_type = details["type"]
    conv_instr = details["instr"]
    block_type = details["block_type"]

    try: param = params[0]
    except: param = None
    try: param2 = params[1]
    except: param2 = None
    try: param3 = params[2]
    except: param3 = None

    # Check if param matches Txxxx or Cxxxx, and then update to TIMxxxx or Cxxxx.
    # Doing this so that it matches with the actual instruction (TIM, CNT)
    if param != None and (re.match(r"T\d{3,4}", param) or re.match(r"C\d{3,4}", param)):
        # print("Timer tag", param)
        if param.find("T") != -1:
            param = "TIM" + param[1:] # Required to match the actual instruction
        elif param.find("C") != -1:
            param = "CNT" + param[1:] # Required to match the actual instruction

    # Manage input parameters (e.g. Txxxx, Cxxxx or #xxxx)
    # if line[0] == "@" or line[0] == "#" or line[0] == "&":
    #     print("ONS", line)
    #     ONS_instr = True
    #     line = line[1:]

    # If it's a timer or counter tag, add the .DN bit. Check either TIM/CNT, or Txxxx/Cxxxx using regex
    if param != None and instr.upper() != "RESET" and (param.find("TIM") != -1 or param.find("TTIM") != -1 or param.find("CNT") != -1): 
        NEEDS_DN_BIT = True
    # If it's a timer instruction, add TIM to the tag
    elif line.find("TIM ") != -1: 
        param = "TIM" + param
    elif line.find("TTIM(") != -1: 
        param = "TIM" + param
    # If it's a counter instruction, add CNT to the tag
    elif line.find("CNT ") != -1: 
        param = "CNT" + param
    # If it's a scaling instruction, extract internal parameters
    elif instr_type.upper() == "SCALING":
        # Create additional required parameters (P1, P2, P3, P4) for scaling
        try: 
            # print("Scaling")
            detailed_address = util.expandTag(param2)
            prefix = detailed_address["prefix"]
            number = int(detailed_address["number"])

            p1 = convert_tagname(param2, tagfile, system_name)
            p2 = convert_tagname(prefix + str(number + 1), tagfile, system_name)
            p3 = convert_tagname(prefix + str(number + 2), tagfile, system_name)
            p4 = convert_tagname(prefix + str(number + 3), tagfile, system_name)
        except:
            # print("Failed")
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
        # print("BTD", instr, param, param2)
        ctrl_word = param2
        # Ensure that the destination bit is in the correct format: 4 numbers with leading zeros if needed
        if (ctrl_word.find("#") != -1) or (ctrl_word.find("&") != -1): #Check if it's a hardcoded value (e.g. #10) and remove the #
            ctrl_word = ctrl_word.replace("#", "").replace("&", "")
        # Make sure ctrl_word has 4 digits
        while len(ctrl_word) < 4:
            ctrl_word = "0" + ctrl_word
        # print(ctrl_word)
        if instr == "MOVB(82)":
            source_bit = str(int(ctrl_word[2:4]))
            dest_bit = str(int(ctrl_word[0:2]))
            ctrl_length = "1"
        elif instr == "MOVD(83)":
            dest_bit = str(int(ctrl_word[1])*4)
            source_bit = str(int(ctrl_word[3])*4)
            ctrl_length = str((int(ctrl_word[2])+1)*4) # Input is 0-3 digits, which translates to 4-16 bits
        else:
            source_bit = str(int(ctrl_word[2:4]))
            dest_bit = str(int(ctrl_word[0:2]))
            ctrl_length = "1"

        # print(source_bit, dest_bit, ctrl_length)

    # Convert the tagname
    og_param, og_param2, og_param3 = param, param2, param3
    if param != None:
        param = convert_tagname(param, tagfile, system_name)
    if param2 != None:
        param2 = convert_tagname(param2, tagfile, system_name)
    if param3 != None:
        param3 = convert_tagname(param3, tagfile, system_name)

    # Check to add .DN bit
    if NEEDS_DN_BIT:
        # print("Adding .DN bit to", param, instr_type)
        if instr_type.upper() == "COMPARE" or instr_type.upper() == "OR_COMPARE" or instr_type.upper() == "COMPARE_OLD":
            param = param + ".ACC"
            catchErrors["error"] = True
            catchErrors["message"] = "WARNING: .ACC VALUE AND COMPARATOR NEED TO BE INVERTED FROM OMRON TO AB. ie. LESS THAN 8 (out of 10) because GRT THAN 2"
        else:
            param = param + ".DN"

    # Manage & Covnert Instructions
    if instr_type.upper() == "IGNORE":

        # print("Non-convertable instruction: ", instr)
        catchErrors["error"] = True
        catchErrors["message"] = "Non-convertable instruction: " + instr
        catchErrors["list"].append(line)

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
        if (param.find("#") != -1) or (param.find("&") != -1): #Check if it's a hardcoded value (e.g. #10) and remove the #
            param = param.replace("#", "").replace("&", "")
        converted_instruction = conv_instr + "(" + param + "," + param2 + ")"
    # For word copy instructions like XFER (->COP)
    elif instr_type.upper() == "MOVE":
        if (param.find("#") != -1) or (param.find("&") != -1): #Check if it's a hardcoded value (e.g. #10) and remove the #
            param = param.replace("#", "").replace("&", "")
            # Omron arguments are Length, Source, Destination
            # AB arguments are Source, Destination, Length
        converted_instruction = conv_instr + "(" + param + "," + param2 + ")"
   
    elif instr_type.upper() == "COPY":
        # print("Copy instruction")
        if (param.find("#") != -1) or (param.find("&") != -1): #Check if it's a hardcoded value (e.g. #10) and remove the #
            param = param.replace("#", "").replace("&", "")
            # Omron arguments are Length, Source, Destination
            # AB arguments are Source, Destination, Length
        # print(instr)
        converted_instruction = conv_instr + "(" + param2 + "," + param3 + "," + param + ")"
        # print(converted_instruction)


    elif instr_type.upper() == "FILL":
        if (param.find("#") != -1) or (param.find("&") != -1): #Check if it's a hardcoded value (e.g. #10) and remove the #
            param = param.replace("#", "").replace("&", "")
            # Omron arguments are Length, Source, Destination
            # AB arguments are Source, Destination, Length
        # print("BSET", param, param2, param3, og_param, og_param2, og_param3)
        try:
            # detailed_address = util.expandTag(og_param2)
            # prefix = detailed_address["prefix"]
            # number = int(detailed_address["number"])

            start_addr = int(og_param2.replace("D", "").replace("W", "").replace("A", ""))
            end_addr = int(og_param3.replace("D", "").replace("W", "").replace("A", ""))
            ctrl_length = str(end_addr - start_addr + 1)
        except:
            ctrl_length = "1"
        converted_instruction = conv_instr + "(" + param + "," + param2 + "," + ctrl_length + ")"

    
    # For BTD instructions like MOVB, MOVD
    elif instr_type.upper() == "BTD":
        # Omron arguments are Source, Bit Designation, Destination
        # AB arguments are Source, Source Bit, Destination, Destination Bit, Length
        converted_instruction = conv_instr + "(" + param + "," + source_bit + "," + param3 + "," + dest_bit + "," + ctrl_length + ")"
        # print(converted_instruction)

    # For output intsructions like OUT, SET, RSET
    elif instr_type.upper() == "OUTPUT": 
        converted_instruction = conv_instr + "(" + param + ")"
    # For math instructions like ADD, SUB, MUL, SCL
    elif instr_type.upper() == "MATH": 
        #Check if it's a hardcoded value (e.g. #10) and remove the #
        if (param.find("#") != -1) or (param.find("&") != -1): #Check if it's a hardcoded value (e.g. #10) and remove the #
            param = param.replace("#", "").replace("&", "")
        else: param = param
        if (param2.find("#") != -1) or (param2.find("&") != -1): #Check if it's a hardcoded value (e.g. #10) and remove the #
            param2 = param2.replace("#", "").replace("&", "")
        else: param2 = param2
        converted_instruction = conv_instr + "(" + param + "," + param2 + "," + param3 + ")"

    elif instr_type.upper() == "INCREMENT":
        converted_instruction = conv_instr + "(" + param + "," + "1" + "," + param + ")"

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
        converted_instruction = conv_instr + "(" + param.replace(".","_") + "_storage" + "," + param + ")"

    elif instr_type.upper() == "TIMER" or instr_type.upper() == "RET_TIMER":
        if (param2.find("#") != -1) or (param2.find("&") != -1):
            # Convert from 1/10th sec to ms
            preset = str(int(int(param2.replace("#", "").replace("&", "")) * 1000 / 10)) 
        else:
            preset = param2
        # if param3 != None: # For RET_TIMER instructions - not needed
        #     converted_instruction = conv_instr + "(" + param + "," + preset + "," + "0" + ")" + f"XIC({param3})RES({param})"
        # else:
        converted_instruction = conv_instr + "(" + param + "," + preset + "," + "0" + ")"

    elif instr_type.upper() == "COUNTER":
        if (param2.find("#") != -1) or (param2.find("&") != -1): #Check if it's a hardcoded value (e.g. #10) and remove the #
            preset = param2.replace("#", "").replace("&", "")
        else:
            preset = param2
        converted_instruction = "ONS(" + system_name + "_oneShots[" + str(one_shot_index) + "])" 
        # Make sure to increment global one shot index
        one_shot_index += 1
        converted_instruction += conv_instr + "(" + param + "," + preset + "," + "0" + ")"
    
    elif instr_type.upper() == "SPECIAL_RESET":
        converted_instruction = ""
        # print("Special Reset instruction", og_param, og_param2)
        try:
            start_addr = int(og_param.replace("CNT", "").replace("C", ""))
            end_addr = int(og_param2.replace("CNT", "").replace("C", ""))
            ctrl_length = end_addr - start_addr + 1
            # print(ctrl_length)
        except:
            ctrl_length = 1
        # Now build out multiple branched Resets
        if ctrl_length > 1:
            converted_instruction = "["

        for i in range(ctrl_length):
            in_param = "C" + str(int(start_addr) + i)
            out_param = convert_tagname(in_param, tagfile, system_name)
            converted_instruction += conv_instr + "(" + out_param + "),"

        if ctrl_length > 1:
            converted_instruction = converted_instruction[:-1] + "]" # Remove the comma for the last one
        else: 
            converted_instruction = converted_instruction[:-1] # Remove the comma for the last one
        # else:
        #     converted_instruction = conv_instr + "(" + param + ")"
        # print(converted_instruction)

    elif instr_type.upper() == "RESET":
        converted_instruction = conv_instr + "(" + param + ")"

    elif instr_type.upper() == "COMPARE" or instr_type.upper() == "OR_COMPARE":
        if (param2.find("#") != -1) or (param2.find("&") != -1): #Check if it's a hardcoded value (e.g. #10) and remove the #
            param2 = param2.replace("#", "").replace("&", "")
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
        param = param.replace("#", "").replace("&", "")

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
        # print("ONS instr")
        if block_type == "IN":
            converted_instruction = converted_instruction + "ONS(" + system_name + "_oneShots[" + str(one_shot_index) + "])"
        elif block_type == "OUT":
            converted_instruction = "ONS(" + system_name + "_oneShots[" + str(one_shot_index) + "])" + converted_instruction
        else:
            converted_instruction = "ONS(" + system_name + "_oneShots[" + str(one_shot_index) + "])" + converted_instruction
        # Make sure to increment global one shot index
        one_shot_index += 1

    return converted_instruction, catchErrors

def convert_tagname(address: str, tagfile: pd.DataFrame, system_name:str):
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
    elif address.find("TIM") != -1:
        address = address.replace("TIM", "T")
        address = "T" + str(int(address[1:])) # Required shortening to match tag lookup file (eg. T0090 -> T90)
    elif address.find("CNT") != -1:
        address = address.replace("CNT", "C")
        address = "C" + str(int(address[1:])) # Required shortening to match tag lookup file (eg. C0090 -> C90)

    # if it's a hardcoded value (e.g. #10), return the value as is
    if address.find("#") != -1 or address.find("&") != -1: # Do not convert hardcoded values
        return address
    if address.find("P_") != -1: # Do not convert System Parameters (P_on, P_First_Cycle, etc.)
        return address   
    else:
        # Search the tagfile for the address
        try:
            query = tagfile.query(f'address == "{address}"')
        except:
            query = None
        # if address.find("HR") >= 0 or address.find("AR") >= 0:
        # elif address.isnumeric() or address.find(".") >= 0:
            # print(1)
            # query = tagfile.query(f'address == "{address}"')
        # else:
            # print(2)
            # query = tagfile.query(f'address == "{address}"')
        # print(query)
        if query.empty:
            converted_tagname = ""
            # split = address.split(".")
            converted_tagname = system_name + "_ADDR_" + address
            # for word in split:
            #     if word == split[-1]: converted_tagname += word
            #     else: converted_tagname = tagname + word + "_"
        else:
            converted_tagname = query["tagname"].to_string(index=False)
        
        # Add converted tagname to the global array if needed
        if INDIRECT_ADDRESS:
            converted_tagname = system_name + "Global_Array[" + converted_tagname + "]" 
            INDIRECT_ADDRESS = False

        # print(converted_tagname)
        return converted_tagname

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
    # line = line.replace("@" , "")
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

