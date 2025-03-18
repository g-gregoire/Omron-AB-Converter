import lookup as lk

from typing import List

class Block:
    def __init__(self, logic: List[str]=[], block_type: str="", blocks_in: int=0):
        self.content = {
            "logic": logic,
            "type": block_type,
            "blocks_in": blocks_in
        }
        self.converted_logic = ""
        # print("Block created. Logic: ", self.logic)

    def __str__(self) -> str:
        logic = str(self.content["logic"])
        return logic
        # return f"{self.logic}" # old structure
    
    def addLine(self, logic: str):
        self.content["logic"].append(logic)
        # self.logic.append(block) # old structure
        # print("Line updated. Logic: ", self.logic)

    def addContent(self, logic, block_type, blocks_in):
        self.content["logic"] = logic
        self.content["block_type"] = block_type
        self.content["blocks_in"] = blocks_in

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

    # def convertBlocks(self):
    #     for index, block in enumerate(self.blocks):
    #         print(block)

    #         break


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