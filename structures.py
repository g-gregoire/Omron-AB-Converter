import lookup as lk
import utilities_logic as ul

from typing import List, Dict
import re

class Block:
    def __init__(self, details: List[Dict]=[], block_type: str="", blocks_in: int=1):
        if details[0]["logic"]: 
            logic = [item["logic"] for item in details if "logic" in item]
        else: logic = []
        if details == []: self.details = []
        else: self.details = details
        self.logic = logic
        self.converted_block = logic
        if block_type == "": self.block_type = ""
        else: self.block_type = block_type
        if blocks_in == 1: self.blocks_in = 1
        else: self.blocks_in = blocks_in
        # self.converted_logic = ""
        # print("Block created. Logic: ", self.logic)

    def __str__(self) -> str:
        logic = str(self.converted_block)
        return logic
        # return f"{self.logic}" # old structure

    def innerJoin(self):
        logic_details = self.details
        working_logic = []
        types_array = []
        active_OR = False
        # REVERSE PASS
        for index, line in enumerate(reversed(self.details)):
            logic = line["logic"]
            line_type = line["block_type"]
            types_array.append(line_type)
            # print(logic, "- Type:", line_type)

            if line_type == "START":
                # print("In type. Line: ", logic)
                if active_OR == False:
                    working_logic.append(logic)
                else:
                    working_logic.append(logic)
                    working_logic.append("[")
                    active_OR = False
            elif line_type == "IN":
                # print("In type. Line: ", logic)
                if active_OR == False:
                    working_logic.append(logic)
                else:
                    working_logic.append(logic)
            elif line_type == "OR":
                # print("OR type. Line: ", logic)
                if active_OR == False:
                    working_logic.append("]")
                    working_logic.append(logic)
                    working_logic.append(",")
                    active_OR = True
                else:
                    working_logic.append(logic)
                    working_logic.append(",")
            
            # Check if last line and active_OR is True, then add opening ("closing") bracket
            if index == len(self.details) - 1 and active_OR == True:
                working_logic.append("[")
        
        # Set block type
        if "START" in types_array:
            self.block_type = "START"
        elif "OUT" in types_array:
            self.block_type = "OUT"
        else:
            self.block_type = "IN"
        # print(output_logic)
            
        # # Lastly, if block starts with a , then remove it and set type to OR
        # if working_logic[-1] == ",":
        #     working_logic.pop()
        #     self.block_type = "OR"

        # print(working_logic)
        output_logic = "".join(reversed(working_logic))
        self.converted_block = [output_logic]
        # self.converted_logic = output_logic
        return output_logic

class Rung:
    def __init__(self, original:str="", blocks: List[Block]=[], connectors: List[str]=[], comment: str="", converted_blocks: List[str]=[], num:int=0):
        if original == "": self.original = ""
        else: self.original = original
        if blocks == []: self.blocks = []
        else: self.blocks = blocks
        if connectors == []: self.connectors = []
        else: self.connectors = connectors
        if comment == "": self.comment = ""
        else: self.comment = comment
        self.converted_blocks = []
        self.converted_logic = ""
        self.has_TR_blocks = False
        self.TR_blocks = {}
        if num == 0: self.num = 0
        else: self.num = num

    def __str__(self) -> str:
        return f"{self.blocks} {self.connectors}"
    
    def addOriginal(self, original: str):
        self.original = original
    
    def addBlock(self, block: Block):
        self.blocks.append(block)
        return [], [] # Output used to reset current_details and type_array

    def addConnector(self, connector: str):
        self.connectors.append(connector)

    def addConvertedBlock(self, block: str):
        self.converted_blocks.append(block)

    def addComment(self, comment: str):
        self.comment = comment

    def addConvertedLogic(self, logic: str):
        self.converted_logic = logic

    def viewBlocks(self, text: str=""):
        if text != "":
            print("\n" + text)
        else:
            print("")
        if len(self.blocks) == 1:
            print("Block:\n", self.blocks[0].converted_block[0])
        else:
            print(len(self.blocks), "Blocks:")
            for block in self.blocks:
                print(block)

    def viewRung(self):
        print("Comment: ", self.comment)
        print("Blocks:")
        for block in self.blocks:
            print(block)
        # for connector in self.connectors:
        # print("Connectors: ")
        # print(self.connectors)
        print("Converted Blocks: ")
        print(self.converted_blocks)
        print("Converted Logic: ")
        print(self.converted_logic)

    def join2Blocks(self, index1, index2, connector: str):
        block1 = self.blocks[index1]
        block2 = self.blocks[index2]
        # print("Joining 2 blocks,", connector)
        # print(block1)
        # print(block2)
        # print(connector)
        if connector == "AND":
            self.blocks[index1] = self.simpleJoin(block1, block2, "AND")
        elif connector == "OR":
            self.blocks[index1] = self.simpleJoin(block1, block2, "OR")
        self.blocks.pop(index2)

    def join3Blocks(self, index1, index2, index3, instr_type: str):
        # This function is for special cases like counters, KEEP, and TTIM that have two inputs going into it
        block1 = self.blocks[index1]
        block2 = self.blocks[index2]
        try:
            block3 = self.blocks[index3]
        except:
            block3 = None
        # print("Joining 3 blocks")
        # print("Line 1:", block1.converted_block[0])
        # print("Line 2:", block2.converted_block[0])
        # print("Line 3:", block3.converted_block[0])

        # Extract instruction Tag from Counter/Timer
        # print("Block 3: ", block3.converted_block[0])
        if instr_type.upper() == "COUNTER":
            # match = re.search(r"CNT\d{3,4}", block3.converted_block[0])
            match = re.search(r"[\w.]+_CTR", block3.converted_block[0]) # Used to match to all counter tags
            # print("Match: ", match)
            if match:
                tag = match.group(0)
            else: tag = "???" # Placeholder for error
            reset_instruction = "RES(" + tag + ")"
        elif instr_type.upper() == "KEEP":
            match = re.search(r"OTL\([\w.]+\)", block3.converted_block[0])
            # print("Match: ", match)
            if match:
                # print("Match: ", match.group(0))
                tag = match.group(0)
            else: tag = "OTL(???)" # Placeholder for error
            reset_instruction = tag.replace("OTL", "OTU")
        elif instr_type.upper() == "RET_TIMER":
            match = re.search(r"TIM\d{3,4}", block3.converted_block[0])
            if match:
                tag = match.group(0)
            else: tag = "???" # Placeholder for error
            reset_instruction = "RES(" + tag + ")"
        reset_block = Block([{"logic": reset_instruction}], "OUT", 1) # Create a reset block
        temp_block1 = self.simpleJoin(block1, block3, "AND") # Join the first block and the counter
        temp_block2 = self.simpleJoin(block2, reset_block, "AND") # Join the second block and the reset block
        final_block = self.simpleJoin(temp_block1, temp_block2, "OR") # Join the two new blocks
        final_block.block_type = "OUT"
        self.blocks[index3] = final_block
        self.blocks[index3].details[0]["type"] = "output"
        # print("Final Block: ", final_block.details)
        self.blocks.pop(index2)
        self.blocks.pop(index1)


    def simpleJoin(self, block1:Block, block2:Block, connect_type="AND"):
        details = {}
        logic = []
        converted_block = []
        block_type = ""
        blocks_in = 1

        if connect_type == "AND":
            if block1.converted_block[0][-1] == "]" and block2.converted_block[0][0] == ",": # Adding for edge case where OR block with leading , needs to be grouped
                # print("Joining already OR'd block")
                converted_block = block1.converted_block[0][:-1] + block2.converted_block[0]
            else:
                converted_block = block1.converted_block[0] + block2.converted_block[0]
        elif connect_type == "OR":
            if block1.converted_block[0][0] == "[" and block1.converted_block[0][-1] == "]": # Added for cases where two OR blocks are OR'd together, reduce double brackets
                # print("Joining already OR'd block")
                converted_block = block1.converted_block[0][:-1] + "," + block2.converted_block[0] + "]"
            else:
                converted_block = "[" + block1.converted_block[0] + "," + block2.converted_block[0] + "]"
        else:
            converted_block = block1.converted_block[0] + block2.converted_block[0]
        block_type = ul.determine_block_type([block1.block_type, block2.block_type])
        blocks_in = block1.blocks_in
        details["logic"] = converted_block
        details["converted_block"] = converted_block
        details["block_type"] = block_type
        details["blocks_in"] = blocks_in

        # print("Joined block: ", [details])
        joined_block = Block([details], block_type, blocks_in)
        return joined_block

    def createSubSet(self, start_index:int, end_index:int) -> List[Block]:
        subset = self.blocks[start_index:end_index]
        return subset

class Routine:
    def __init__(self, rungs: List[Rung]=[]):
        if rungs == []: self.rungs = []
        else: self.rungs = rungs

    def addRung(self, rung: Rung):
        self.rungs.append(rung)

    def viewRungs(self):
        for rung in self.rungs:
            print("Printing all rungs: ")
            if rung.comment != "":
                print("Comment: ", rung.comment)
            print(rung.original)

# Testing
# test_block1 = Block(["XIC(IR1.0)"])
# test_block2 = Block(["XIO(IR1.5)"])

# # print(test_block1)
# rung = Rung()
# rung.addBlock(test_block1)
# rung.addBlock(test_block2)
# rung.addConnector("AND")
# print(rung)