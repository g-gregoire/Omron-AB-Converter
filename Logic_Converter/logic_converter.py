import file_functions as ff
import lookup as lk
from structures import Rung, Block

import pandas as pd
from pprint import pprint
import re


EOL = "^^^"
NL = "\n"
SP = " "
END = ";"

def loop_rungs(logic_file: pd.DataFrame, output_file, tagfile, view_rungs = False, start_rung=0, num_rungs=-1):
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
        rung, end_of_rung = getRung(row['logic'], rung)
        # print(rung)

        # Once the end of the rung is reached, decode the entire rung
        if end_of_rung:
            # print(rung)
            if rung_num <= start_rung-1:
                rung = ""
                continue

            # Call function to break the rung into blocks
            rung_blocks = blockBreaker(rung, catchErrors)
            # Call function to convert the blocks
            converted_rung, catchErrors = convertBlocks(rung_blocks, catchErrors, tagfile)
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
            
    return catchErrors

def getRung(text: str, rung: str):
    # Check if the end of the rung is reached (^^^) and set the flag true
    if text == EOL:
        end_of_rung = True

    # Otherwise, add the text to the rung and new line
    else: 
        end_of_rung = False
        rung += text + NL

    return rung, end_of_rung

def blockBreaker(rung: str, catchErrors: dict):
    # This function splits rung into logic/load blocks

    # print(rung)
    # Create structures to use
    outputRung = Rung()
    startRung = False
    OUTPUT_BLOCK = False
    # Split instructions into an array; exclude the last empty string
    rung = rung.split(NL)[:-1]

    # Check for comments
    if rung[0][0] == "'":
        outputRung.addComment(rung[0])
        # print(rung[0])
        rung = rung[1:]

    # Loop through each instruction in the rung
    for index, line in enumerate(rung):
        # print(line)
        # Extract current line
        instr, param, instr_type, conv_instr,_,_ = extractLine(line)
        
        # Skip instruction if it's CLC(41)
        if instr == "CLC(41)":
            continue

        # Extract previous line
        try: 
            prev_line = rung[index-1]
            prev_instr, prev_param, prev_instr_type, prev_conv_instr = extractLine(prev_line)
        except: 
            prev_line = prev_instr = prev_param = prev_instr_type = prev_conv_instr = None
        # Extract next line
        try:
            next_line = rung[index+1]
            next_instr, next_param, next_instr_type, next_conv_instr,_,_ = extractLine(next_line)
        except:
            next_line = next_instr = next_param = next_instr_type = next_conv_instr = None
        # Extract after next line
        try:
            after_next_line = rung[index+2]
            after_next_instr, after_next_param, after_next_instr_type, after_next_conv_instr,_,_ = extractLine(after_next_line)
        except:
            after_next_line = after_next_instr = after_next_param = after_next_instr_type = after_next_conv_instr = None

        # If parameter matches pattern TRx where x is a number, using regex
        if param != None and re.match(r"TR\d", param):
            # print("TR Block")
            if instr == "OUT":
                if len(block.logic) > 0:
                    outputRung.addBlock(block) # Add the old block to the rung
                block = Block() 
                block.addLine("STBR") # This is used to artifically add an Start Branch (STBR) block
                outputRung.addBlock(block)
                block = Block()
                continue
            elif instr == "LD":
                if len(block.logic) > 0:
                    outputRung.addBlock(block) # Add the old block to the rung
                block = Block() 
                block.addLine("NWBR") # This is used to artifically add an Start Branch (NWBR) block
                outputRung.addBlock(block)
                block = Block()
                continue

        # If next block is a counter, create a new block since this involves a CTU instruction and a Reset instruction
        if next_line and next_instr_type.upper() == "COUNTER":
            # print("Counter is next")
            # print(next_line)
            if len(block.logic) > 0:
                outputRung.addBlock(block) # Add the old block to the rung
            block = Block() # Create a new block
            new_block = Block() # Create a separate block from the current thread
            new_block.addLine(next_line)
            outputRung.addBlock(new_block) # Add the current output block to the rung
            block = Block()
            block.addLine("ANDLD") # This is used to artifically add an ANDLD block
            outputRung.addBlock(block)
            block = Block()

        # Required since the counter instruction is split into 2 lines (CTU and RES)
        if instr_type.upper() == "COUNTER":
            # print("Counter")
            line = line.replace("CNT", "RESET")
            # print(line)
        
        if instr_type.upper() == "COMPARE":
            # print("Compare")
            if len(block.logic) > 0:
                outputRung.addBlock(block) # Add the old block to the rung
            block = Block() # Create a new block
            # Determine which comparison is being used
            EQU = GRT = LES = False
            if next_line == None: # Added for strange coding where CMP and comp_type are on different rungs
                # print("End of rung")
                catchErrors["error"] = True
                catchErrors["list"].append(line)
                outputRung.comment += f" - ERROR CONVERTING THIS RUNG ({instr})."
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
                    rung.pop(index+1)
                    rung.pop(index+1)
                    rung.pop(index+1)
                elif EQU and LES:
                    # print("LEQ")
                    line = line.replace("CMP(20)", "LEQ")
                    # Pop next 3 lines
                    rung.pop(index+1)
                    rung.pop(index+1)
                    rung.pop(index+1)
                elif EQU:
                    # print("EQU")
                    line = line.replace("CMP(20)", "EQU")
                    # Pop next line
                    rung.pop(index+1)
                elif GRT:
                    # print("GRT")
                    line = line.replace("CMP(20)", "GRT")
                    # Pop next line
                    rung.pop(index+1)
                elif LES:
                    # print("LES")
                    line = line.replace("CMP(20)", "LES")
                    # Pop next line
                    rung.pop(index+1)

        if instr == "LD" or instr == "LDNOT":
            if not startRung:
                # print("Start Rung")
                startRung = True
                block = Block()
                block.addLine(line)
                # outputRung.addConnector("START")
                # outputRung.viewRung()
            else:
                # print("New Block")
                if len(block.logic) > 0:
                    outputRung.addBlock(block) # Add the old block to the rung
                block = Block() # Create a new block
                block.addLine(line)

        elif instr == "OR" or instr == "ORNOT":
            # print("New Block - OR")
            if len(block.logic) > 0:
                outputRung.addBlock(block) # Add the old block to the rung
            block = Block()
            block.addLine(line) # This is used to add the current block
            outputRung.addBlock(block)
            block = Block() 
            block.addLine("ORLD") # This is used to artifically add an ORLD block
            outputRung.addBlock(block)
            block = Block()

        elif instr == "ANDLD" or instr == "ORLD":
            if len(block.logic) > 0:
                outputRung.addBlock(block) # Add the old block to the rung
            block = Block()
            block.addLine(instr)
            outputRung.addBlock(block)
            block = Block()

        # Keep instruction - needs to be broken up into OTL and OTU
        elif instr_type.upper() == "KEEP":
            # print("keep")
            insert_index = findLastLD(outputRung)
            if insert_index != -1:
                # Insert OTL instruction before the last LD instruction
                block = Block()
                block.addLine(line)
                outputRung.blocks.insert(insert_index, block)
                block = Block() 
                block.addLine("ANDLD") # This is used to artifically add an ORLD block
                outputRung.blocks.insert(insert_index+1, block)
                block = Block()
                # Insert OTU instruction in the Keep block
                block = Block()
                line = line.replace("KEEP(11)", "OTU")
                block.addLine(line)
                outputRung.addBlock(block) # Add the OTU block to the rung
                block = Block() 
                block.addLine("ANDLD") # This is used to artifically add an ORLD block
                outputRung.addBlock(block)
                block = Block()
                block.addLine("ORLD") # This is used to artifically add an ORLD block
                outputRung.addBlock(block)
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
                outputRung.addBlock(block) # Add the current output block to the rung
                block = Block() # Create a new block
                block.addLine("ORLD") # This is used to artifically add an ORLD block
                outputRung.addBlock(block)
                block = Block()
            elif checkMultipleOutputs(rung) and not OUTPUT_BLOCK:
                # print(2)
                if len(block.logic) > 0:
                    outputRung.addBlock(block) # Add the current output block to the rung
                block = Block() # Create a new block
                block.addLine(line)
                outputRung.addBlock(block) # Add the current output block to the rung
                block = Block() # Create a new block
                OUTPUT_BLOCK = True
            # Output block is active but previous instruction was "AND" 
            elif len(block.logic) > 0 and OUTPUT_BLOCK and (prev_instr == "AND" and prev_instr == "ANDNOT"):
                # print(3)
                # outputRung.addBlock(block) # Add the old block to the rung
                # block = Block() # Create a new block
                block.addLine(line)
                outputRung.addBlock(block) # Add the current output block to the rung
                block = Block() # Create a new block
                # if next_line == None:
                    # print(3.5)
                block = Block() # Create a new block
                block.addLine("ORLD") # This is used to artifically add an ORLD block
                    # outputRung.addBlock(block)
                    # OUTPUT_BLOCK = False
            elif OUTPUT_BLOCK:
                # print(4)
                block.addLine(line)
                if len(block.logic) > 0:
                    outputRung.addBlock(block) # Add the current output block to the rung
                block = Block() # Create a new block
                block.addLine("ORLD") # This is used to artifically add an ORLD block
                outputRung.addBlock(block)
                block = Block()
                if next_line == None:
                    # print(4.5)
                    # block = Block() # Create a new block
                    # block.addLine("ORLD") # This is used to artifically add an ORLD block
                    # outputRung.addBlock(block)
                    OUTPUT_BLOCK = False
            else:
                # print(5)
                block.addLine(line)
                outputRung.addBlock(block) # Add the current output block to the rung
                block = Block() # Create a new block

        else:
            # print(6)
            block.addLine(line) # Add any non-specific lines to the block

        if index == len(rung) - 1:
            # Append the last block to the rung
            if len(block.logic) > 0:
                outputRung.addBlock(block) # Add the old block to the rung
            # print("End of Rung")
    
    # outputRung.viewRung()
    return outputRung

def convertBlocks(rung: Rung, catchErrors: dict, tagfile: pd.DataFrame):
    # This function converts the blocks in a rung
    for index, block in enumerate(rung.blocks):
        # print(block)
        converted_logic = ""
        OR_BLOCK = False

        # Loop through each instruction in the block
        for index, line in enumerate(block.logic):
            # print(line)
            instr, param, instr_type, conv_instr,_,_ = extractLine(line) # Extract current line

            if instr == "ORLD" or instr == "ANDLD":
                converted_logic = instr
                rung.addConvertedBlock(converted_logic)
                continue
            try: # Extract next line
                next_line = block.logic[index+1]
                next_instr, next_param, next_instr_type, next_conv_instr,_,_ = extractLine(next_line)
            except: 
                next_line = next_instr = next_param = next_instr_type = next_conv_instr = None
            # Extract next line
            try: 
                after_next_line = block.logic[index+2]
                after_next_instr, after_next_param, after_next_instr_type, after_next_conv_instr,_,_ = extractLine(after_next_line)
            except:
                after_next_line = after_next_instr = after_next_param = after_next_instr_type = after_next_conv_instr = None

            # Begin Conversion
            # Create OR block
            if not OR_BLOCK and (next_instr == "OR" or next_instr == "ORNOT"):
                OR_BLOCK = True
                # print("Start OR block")
                converted_logic += "[" 
                # print(converted_logic)
            elif not OR_BLOCK and (next_instr == "AND" or next_instr == "ANDNOT") and (after_next_instr == "OR" or after_next_instr == "ORNOT"):
                OR_BLOCK = True
                # print("Start OR block")
                converted_logic += "[" 
                # print(converted_logic)
            
            # print("Add Logic")
            # Convert the instruction
            converted_instruction, catchErrors = convertInstruction(line, catchErrors, tagfile)
            converted_logic += converted_instruction
            if catchErrors["error"]:
                rung.comment += f" - ERROR CONVERTING THIS RUNG ({instr})."
                catchErrors["error"] = False
            # print(converted_logic)

            # Allow for LD-AD-OR block (LD & AND are part of the first branch)
            if OR_BLOCK and next_instr != "OR" and after_next_instr != "OR": 
                # print("End OR Block")
                converted_logic += "]"
                # print(converted_logic)
                OR_BLOCK = False
            # Don't add anything if the next instruction is an AND within an OR block
            elif OR_BLOCK and (next_instr == "AND" or next_instr == "ANDNOT"): 
                continue
            # If it's an OR block and it's not the end of the block, add a comma
            elif OR_BLOCK and next_line != None:
                # print("New line - add comma")
                converted_logic += ","
                # print(converted_logic)
            # If the OR block is open and it's the last line, close the OR block
            elif OR_BLOCK and next_line == None: 
                # print("End OR Block")
                converted_logic += "]"
                # print(converted_logic)
                OR_BLOCK = False
            
            if next_line == None: # Last line in the block, add to the rung
                # print("End of block")
                rung.addConvertedBlock(converted_logic)
        # print(converted_logic)
        # break
    # rung.viewRung()

    return rung, catchErrors

def assembleBlocks(rung: Rung):
    # This function assembles the blocks into a rung
    new_rung = rung.converted_blocks.copy()
    new_block = ""
    index = 0
    NUM_BRANCHES = 0 # Used to handle TR branch closing

    while len(new_rung) > 1:
        block = new_rung[index]
        # print(index, block)
        
        if index > 100: # Watchdog break out of infinite loop
            break
        
        # Handle ORLD block
        if block == "ORLD":
            # print(index, block)
            # print(index-1, new_rung[index-1])
            # print(index-2, new_rung[index-2])

            new_block = "[" + new_rung[index-2] + "," + new_rung[index-1] + "]"
            new_rung[index-2] = new_block # Replace the first block with the new block
            new_rung.pop(index-1) # Remove the third block
            new_rung.pop(index-1) # Remove the second block
            # print(new_rung)
            # Reset index
            index = 0
            continue
        
        # Handle ANDLD block
        elif block == "ANDLD":
            # print(index, block)
            # print(index-1, new_rung[index-1])
            # print(index-2, new_rung[index-2])
            new_block = new_rung[index-2] + new_rung[index-1]
            new_rung[index-2] = new_block # Replace the first block with the new block
            new_rung.pop(index-1) # Remove the second block
            new_rung.pop(index-1) # Remove the third block
            # print(new_rung)
            # Reset index and continue
            index = 0
            continue

        # Handle STBR block - Start Branch - these are handled by just removing the block
        elif block == "STBR":
            # if the next instruction is a checking instruction, add a bracket
            if new_rung[index+1].find("XIC") != -1 or new_rung[index+1].find("XIO") != -1:
                new_rung[index+1] = "[" + new_rung[index+1]
            new_rung.pop(index) # Remove the block


        # Handle NWBR block - New Branch - these are handled by just removing the block
        elif block == "NWBR":
            # print(new_rung[index+2])
            # If the following instruction does not have an ORLD, add a comma
            if new_rung[index+2] != "ORLD":
                new_rung[index+1] = "," + new_rung[index+1]
            new_rung.pop(index) # Remove the block


        # If end of rung, without any ORLD or ANDLD, combine the remaining blocks
        if index == len(new_rung) - 1:
            new_block = ""
            index = 0
            while len(new_rung) > 1:
                new_rung[index] = new_rung[index] + new_rung[index+1]
                new_rung.pop(index+1)
            # print(new_block)
        
        # Increment index
        index += 1

    # Add the closing brackets for the TR branches at the end of the rung
    for i in range(NUM_BRANCHES):
        new_rung[0] += "]"
    rung.addConvertedLogic(new_rung[0])
    return rung

def convertInstruction(line: str, catchErrors: dict, tagfile: pd.DataFrame):
    # This function converts an instruction from Omron to AB
    # print(line)
    ONS_instr = False
    NEEDS_DN_BIT = False

    instr, param, instr_type, conv_instr, param2, param3 = extractLine(line)

    if line[0] == "@":
        ONS_instr = True
        line = line[1:]
    # If it's a timer or counter tag, add the .DN bit
    elif param != None and (param.find("TIM") != -1 or param.find("CNT") != -1): 
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
        param = convertTagname(param, tagfile)
    if param2 != None:
        param2 = convertTagname(param2, tagfile)
    if param3 != None:
        param3 = convertTagname(param3, tagfile)

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
        if not (instr == "STBR" or instr == "NWBR"):
            catchErrors["count"] += 1
            catchErrors["list"].append(line)
            catchErrors["error"] = True

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
        converted_instruction = "ONS" + "(" + param + "_ONS" + ")" 
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
        converted_instruction = "ONS" + "(" + param2 + "_ONS" + ")" + converted_instruction

    return converted_instruction, catchErrors

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

def convertTagname(address: str, tagfile: pd.DataFrame):
    # This function searches the tagfile to determine if a converted tagname exists
    # If it does, it returns the converted tagname
    # If it doesn't, it returns the original tagname
    # print(address)
    INDIRECT_ADDRESS = False
    
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
            converted_tagname = address
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

def countInstructions(logic_file: pd.DataFrame):
    # This function counts the number of different instructions in the program,
    # and how many times each instruction is used
    rung = ""
    instr_count = {}
    for rowindex, row in logic_file.iterrows():
        # print(rung_num)
        # Loop through each row and build the rung until the end of the rung
        rung, end_of_rung = getRung(row['logic'], "")
        instr = rung.split(' ')[0]
        # print(instr)
        if instr in instr_count:
            instr_count[instr] += 1
        else:
            instr_count[instr] = 1

    # Order instructions alphabetically
    instr_count = dict(sorted(instr_count.items()))
    pprint(instr_count)
    return instr_count

def findLastLD(rung: Rung):
    # This function finds the last LD index in a block
    return_index = -1
    for index, block in enumerate(rung.blocks):
        for line in block.logic:
            instr, param, instr_type, conv_instr,_,_ = extractLine(line)
            if instr == "LD" or instr == "LDNOT":
                return_index = index
    # print(return_index)
    return return_index


#%% DEPRECATED / NOT USED CODE
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
