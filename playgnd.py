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

num1 = "D480"
# num2 = "480.00"

numbers = ["D482", "D481", "D480"]
df = pd.DataFrame(numbers, columns=["Address"])
# df["Address_num"] = pd.to_numeric(df["Address"], errors="coerce")
print(df.head())
# print type of column
print(type(df["Address"].iloc[0]))
query = df.query(f'Address == {num1}')
if query.empty: print("Empty")
else: print(query)
query2 = df.query(f'Address == "{num1}"')
if query2.empty: print("Empty")
else: print(query2)