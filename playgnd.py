import file_functions as ff
import logic_converter as lc
import lookup as lk

EOL = "^^^"
NL = "\n"
# Open file
wb = ff.openFile()
output = ff.createFile("output", "txt")

rung = ""
for rowindex, row in wb.iterrows():
    rung, flag = lc.getRung(row['logic'], rung)

    if flag:
        # print(rung)
        lc.decodeRung(rung)
        rung = ""
        # Break for testing first rung only
        # break


# Testing - Functions
