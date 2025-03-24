import file_functions as ff
import logic_converter as lc
import utilities as util
import lookup as lk

import os
import pandas as pd

EOL = "^^^"
NL = "\n"
dir = os.getcwd()
# Open file

rng = 2

for i in reversed(range(rng+1)):
    print(f"Idx {i}") 