import lookup as lk

from typing import List, Dict

class Block:
    def __init__(self, details: List[Dict]=[], block_type: str="", blocks_in: int=1):
        if details[0]["logic"]: 
            logic = [item["logic"] for item in details if "logic" in item]
        else: logic = []
        self.details = details
        self.logic = logic
        self.block_type = block_type
        self.blocks_in = blocks_in
        self.converted_block = logic
        # self.converted_logic = ""
        # print("Block created. Logic: ", self.logic)

    def __str__(self) -> str:
        logic = str(self.converted_block)
        return logic
        # return f"{self.logic}" # old structure
    
    # def addLine(self, logic: str):
    #     self.logic.append(logic)

    # def addContent(self, logic, block_type, blocks_in):
    #     self.content["logic"] = logic
    #     self.content["block_type"] = block_type
    #     self.content["blocks_in"] = blocks_in

    def innerJoin(self):
        logic_details = self.details
        working_logic = []
        active_OR = False
        # REVERSE PASS
        for index, line in enumerate(reversed(self.details)):
            logic = line["logic"]
            line_type = line["block_type"]
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

        # print(working_logic)
        output_logic = "".join(reversed(working_logic))
        self.converted_block = [output_logic]
        # self.converted_logic = output_logic
        # Set type to IN
        self.block_type = "IN"
        # print(output_logic)
        return output_logic

class Rung:
    def __init__(self, original:str="", blocks: List[Block]=[], connectors: List[str]=[], comment: str="", converted_blocks: List[str]=[]):
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

    def __str__(self) -> str:
        return f"{self.blocks} {self.connectors}"
    
    def addOriginal(self, original: str):
        self.original = original
    
    def addBlock(self, block: Block):
        self.blocks.append(block)

    def addConnector(self, connector: str):
        self.connectors.append(connector)

    def addConvertedBlock(self, block: str):
        self.converted_blocks.append(block)

    def addComment(self, comment: str):
        self.comment = comment

    def addConvertedLogic(self, logic: str):
        self.converted_logic = logic

    def viewBlocks(self):
        print("\n", len(self.blocks), "Blocks:")
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
        # print("Joining 2 blocks")
        # print(block1.details)
        # print(block2)
        # print(connector)
        if connector == "AND":
            self.blocks[index1] = self.simpleJoin(block1, block2, "AND")
        elif connector == "OR":
            self.blocks[index1] = self.simpleJoin(block1, block2, "OR")
        self.blocks.pop(index2)

    def simpleJoin(self, block1:Block, block2:Block, connect_type="AND"):
        details = {}
        logic = []
        converted_block = []
        block_type = ""
        blocks_in = 1

        if connect_type == "AND":        
            converted_block = block1.converted_block[0] + block2.converted_block[0]
        elif connect_type == "OR":
            converted_block = "[" + block1.converted_block[0] + "," + block2.converted_block[0] + "]"
        else:
            converted_block = block1.converted_block[0] + block2.converted_block[0]
        block_type = block2.block_type # Allow for and IN + OUT block to stay OUT type
        blocks_in = block1.blocks_in
        details["logic"] = converted_block
        details["converted_block"] = converted_block
        details["block_type"] = block_type
        details["blocks_in"] = blocks_in

        # print("Joined block: ", [details])
        joined_block = Block([details], block_type, blocks_in)
        return joined_block

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