# Component files
header = "header.xml"
datatypes = "datatypes.xml"
aoi = "AOIs.xml"
tags = "tags.xml"
routine_header = "routine-header.xml"
footer = "footer.xml"
tagcsv = "tag.csv"

# Lookup conversion fOR Omron to AB
lookup = {
    # Comments
    "'": "Comment",
    # LOAD Instructions
    "LD": ["LOAD", "XIC"],
    "LDNOT": ["LOAD", "XIO"],
    # END LOAD Instructions
    "ORLD": ["LOAD", ""],
    "ANDLD": ["LOAD", "]"],
    # Input AND Instructions
    "AND": ["AND", "XIC"],
    "ANDNOT": ["AND", "XIO"],
    # Input OR Instructions
    "OR": ["OR", "XIC"],
    "ORNOT": ["OR", "XIO"],
    # Branching Instructions
    # "STBR": ["BRANCH", "STBR"],
    # "NWBR": ["BRANCH", "NWBR"],

    # Output Instructions
    "OUT": ["OUTPUT", "OTE"],
    "SET": ["OUTPUT", "OTL"],
    "RSET": ["OUTPUT", "OTU"],
    "DIFU(13)": ["oneshot", "OSR"],
    "DIFD(14)": ["oneshot", "OSF"], 
    "KEEP(11)": ["KEEP", "OTL"],
    "OTU": ["KEEP", "OTU"],

    # Timer Instructions
    "TIM": ["TIMER", "TON"],
    # Count Instructions
    "CNT": ["COUNTER", "CTU"],
    "RESET": ["RESET", "RES"],

    # Comparison Instructions
    "CMP(20)": ["COMPARE", ""],
    "GREATER_THAN": ["COMPARE", "GRT"],
    "P_GT": ["COMPARE", "GRT"],
    "LESS_THAN": ["COMPARE", "LES"],
    "P_LT": ["COMPARE", "LES"],
    "EQUALS": ["COMPARE", "EQU"],
    "P_EQ": ["COMPARE", "EQU"],
    # Converted Comparison Instructions
    "EQU": ["COMPARE", "EQU"],
    "GRT": ["COMPARE", "GRT"],
    "GEQ": ["COMPARE", "GEQ"],
    "LES": ["COMPARE", "LES"],
    "LEQ": ["COMPARE", "LEQ"],

    # Math Instructions
    "ADD(30)": ["math", "ADD"],
    "SUB(31)": ["math", "SUB"],
    "MUL(32)": ["math", "MUL"],
    "DIV(33)": ["math", "DIV"],
    # Binary Math
    "ADB(50)": ["math", "ADD"],
    "SBB(51)": ["math", "SUB"],
    "MLB(52)": ["math", "MUL"],
    "DVB(53)": ["math", "DIV"],
    # Binary Math
    "ANDW(34)": ["math", "AND"],
    
    # Scaling Instructions
    "SCL(64)": ["scaling", "CPT"],

    # PID Instructions
    "PID(60)": ["pid", "PID"],

    # Logical Instructions
    "MOV(21)": ["logical", "MOV"],
    "BIN(23)": ["logical", "MOV"],
    "BCD(24)": ["logical", "MOV"],
    "XFER(70)": ["copy", "COP"],
    "MOVB(82)": ["btd", "BTD"],

    # Other Instructions - No 1:1 conversion
    # "CLC(41)": ["other", "CLC"],
    # "BIN(23)": ["other", "BIN"], # Binary to BCD
    # "BCD(24)": ["other", "BCD"], # BCD to Binary
    # "ADB(50)": ["other", "ADB"],
    # "SCL(64)": ["other", "SCL"],

    # PID Instructions
    # "PID(60)": ["pid", "PID"],

    # End of rung
    "^^^": ";\n",

    "AND<(310)":	["LT",	"COMPARE"],
    "AND<=(315)":	["LE",	"COMPARE"],
    "AND=(300)":	["EQ",	"COMPARE"],
    "AND=L(300)":	["EQU",	"COMPARE"],
    "AND>(320)":	["GT",	"COMPARE"],
    "AND>=(325)":	["GE",	"COMPARE"],
    "CMP(20)":	["CMP",	"COMPARE"],
    "CMPL(60)":	["CMP",	"COMPARE"],
    "LD<(310)":	["LT",	"COMPARE"],
    "LD<=(315)":	["LE",	"COMPARE"],
    "LD=(300)":	["EQ",	"COMPARE"],
    "LD>(320)":	["GT",	"COMPARE"],
    "LD>=(325)":	["GE",	"COMPARE"],
    "BCD(24)":	["TO_BCD",	"Copy"],
    "BCDL(59)":	["MOV",	"Copy"],
    "BIN(23)":	["BCD_TO",	"Copy"],
    "BSET(71)":	["FLL",	"Copy"],
    "MOV(21)":	["MOV",	"Copy"],
    "MOVB(82)":	["MOVB",	"Copy"],
    "MOVD(83)":	["MOV",	"Copy"],
    "MOVL(498)":	["MOV",	"Copy"],
    "XFER(70)":	["COP",	"Copy"],
    "XFRB(62)":	["COP",	"Copy"],
    "CNR(545)":	["RES",	"Counter"],
    "CNT":	["CTU",	"Counter"],
    "RESET":	["RES",	"Counter"],
    "ANDLD":	["XIC",	"Load"],
    "LD":	["XIC",	"Load"],
    "LDNOT":	["XIO",	"Load"],
    "ORLD":	["XIC",	"Load"],
    "AND":	["XIC",	"Logic"],
    "ANDNOT":	["XIO",	"Logic"],
    "ANDW(34)":	["AND",	"Logic"],
    "OR":	["XIC",	"Logic"],
    "ORNOT":	["XIO",	"Logic"],
    "PMCR(260)":["",	"Macro"],
    "-B(414)":	["SUB",	"Math"],
    "*(420)":	["MUL",	"Math"],
    "*B(424)":	["MUL",	"Math"],
    "/(430)":	["DIV",	"Math"],
    "/BL(435)":	["DIV",	"Math"],
    "/UL(433)":	["DIV",	"Math"],
    "+(400)":	["ADD",	"Math"],
    "+B(404)":	["ADD",	"Math"],
    "+BCL(407)":	["ADD",	"Math"],
    "+C(402)":	["ADD",	"Math"],
    "+CL(403)":	["ADD",	"Math"],
    "+L(401)":	["ADD",	"Math"],
    "ADB(50)":	["ADD",	"Math"],
    "ADD(30)":	["ADD",	"Math"],
    "APR(69)":	["CPT",	"Math"],
    "CADD(730)":	["?",	"Math"],
    "DIV(33)":	["DIV",	"Math"],
    "DVB(53)":	["DIV",	"Math"],
    "MLB(52)":	["MUL",	"Math"],
    "MUL(32)":	["MUL",	"Math"],
    "SBB(51)":	["SUB",	"Math"],
    "SUB(31)":	["SUB",	"Math"],
    "DIFD(14)":	["OSF",	"oneshot"],
    "DIFU(013)":	["OSR",	"oneshot"],
    "DIFU(13)":	["OSR",	"oneshot"],
    "OR<=(315)":	["LEQ*", "OR-COMPARE"],
    "OR=(300)":	["EQU*", "OR-COMPARE"],
    "OR>(320)":	["GRT*", "OR-COMPARE"],
    "OR>=(325)":	["GEQ*", "OR-COMPARE"],
    "KEEP(11)":	["OTL",	"Output"],
    "OTU":	["OTU",	"Output"],
    "OUT":	["OTE",	"Output"],
    "RSET":	["OTU",	"Output"],
    "SET":	["OTL",	"Output"],
    "PID(190)":	["PID",	"PID"],
    "PID(60)":	["PID",	"PID"],
    "SCL(194)":	["SCL",	"Scaling"],
    "SCL(64)":	["SCL",	"Scaling"],
    "FIFO(633)":	["FFU",	"Stack"],
    "PUSH(632)":	["FFL",	"Stack"],
    "SSET(630)":	["?",	"Stack"],
    "DATE(735)":	["?",	"System"],
    "TIM":	["TON",	"Timer"],
    "TTIM(87)":	["RTO",	"Timer"],
}
