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

num = 10
i = 0

while i < num:
    print(f"i: {i}")
    if i == 5:
        print("changing i to 8")
        i = 8
        continue
    i += 1