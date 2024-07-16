# Lookup conversion for Omron to AB

lookup = {

"'" : "Comment",
# Basic Inputs
"LD" : ["XIC", "in"],
"LDNOT" : ["XIO", "in"],
"ANDNOT" :  ["XIO", "in"],
"AND" :  ["XIC", "in"],
"OR" : [",XIC", "in"],
"ORNOT" : [",XIO", "in"],
# Branching operators
"ANDLD" :  ["]", "branch"],
"ORLD" :  ["", "branch"],
# Comparisons
"CMP" :  ["", "compare"],
"GREATER_THAN" : ["", "compare"],
"LESS_THAN" : ["", "compare"],
"EQUALS" :  ["", "compare"],
# Timers and Counters
"TIM" :  ["", "count"],
"CNT" :  ["", "count"],
# Outputs
"OUT" : ["OTE", "output"],
"SET" : ["OTL", "output"],
"RSET" : ["OTU", "output"],
"KEEP" :  ["OTL", "output"],
# Modifiers
"ADD" :  ["", "math"],
"MOV" :  ["", "math"],
# Non-Standard
"DIFU" :  ["", "unknown"],
"DIFD" :  ["", "unknown"],
"XFER" :  ["", "unknown"],

# End of line
"^^^" : ";\n"

}