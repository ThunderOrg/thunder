from dictionary import *

constants = Dictionary()

def parseConfig(fname):
    fp = open(fname, 'r')
    lines = fp.readlines()
    for line in lines:
        # remove any leading or ending spaces
        line = line.strip()
        if (line != ""):
            keyval = line.split(":")
            key = keyval[0].strip()
            val = keyval[1].strip()
            cIndex = -1
            # remove any ending comments
            for i in range(0, len(val), 1):
                if (val[i] == '#'):
                    cIndex = i
                    break
            val = val[:cIndexi-1].strip()
            constants.append([key, val])
