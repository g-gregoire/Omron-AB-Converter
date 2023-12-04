file_path = "/Users/georgesgregoire/Documents/Code/Python/Omron-AB-Converter/input.txt"

with open(file_path, "r") as file:
    for line in file:
        print(line.strip())
