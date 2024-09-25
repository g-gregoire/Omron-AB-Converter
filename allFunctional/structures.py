import lookup as lk

from typing import List

# class Phase:
    #Basic Properties
    # def __init__(self, name, number, tag, description="", steps={}, step_detail = [], EM={}, alarms={}, EM_detail=[], permissives=[], rpt_parameters=[], phase_parameters=[], report=[], alarm_detail=[]):
    #     self.name = name
    #     self.number = number
    #     self.tag = tag
    #     self.description = description
    #     self.steps = steps
    #     self.step_detail = step_detail
    #     self.EM = EM
    #     self.EM_detail = EM_detail
    #     self.permissives = permissives
    #     self.rpt_parameters = rpt_parameters
    #     self.phase_parameters = phase_parameters
    #     self.report = report
    #     self.alarms = alarms
    #     self.alarm_detail = alarm_detail
        
    # def __str__(self) -> str:
    #     return self.name
    
    # @property
    # def unit(self):
    #     return self.name.split("-")[0]

class Block:
    def __init__(self, logic: List[str]=[]):
        if logic == []: self.logic = []
        else: self.logic = logic
        # print("Block created. Logic: ", self.logic)
        

    def __str__(self) -> str:
        return f"{self.logic}"
    
    def addLine(self, block: str):
        self.logic.append(block)
        # print("Line updated. Logic: ", self.logic)

class Rung:
    def __init__(self, blocks: List[Block]=[], connectors: List[str]=[], comment: str="", converted_blocks: List[str]=[]):
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

    
# Testing
# test_block1 = Block(["XIC(IR1.0)"])
# test_block2 = Block(["XIO(IR1.5)"])

# # print(test_block1)
# rung = Rung()
# rung.addBlock(test_block1)
# rung.addBlock(test_block2)
# rung.addConnector("AND")
# print(rung)