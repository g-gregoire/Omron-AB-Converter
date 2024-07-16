import file_functions as f
import logic_snippets as lgc
import routine_components as rt

def createFile(phase, tagfile, output_filename=None, output_ext="txt", phasetag_only = False):

    file = f.createfile(output_filename, output_ext)
    file = f.addContext(file, phase)

    rnum = 0 # Initialize rung number
    snum = 1 # Initialize Section number

def createTags(tagList, tagFile, output_filename=None, output_ext="txt"):

    for tag in tagList:

        tagFile = f.addTag(tag['symbol'], tag['description'] , tag['type'], tagFile)
        # print(tag['symbol'], tag['description'], tag['type'])

    tagFile.close()

    return tagFile