import sys
import binascii
import re

def int2byte(i):
    if sys.version_info < (3,):
        return chr(i)
    return bytes((i,))

def byte2int(v):
    if isinstance(v, int):
        return v
    return ord(v)

#check hex string
def parseHexString(inputString, numBytes):
    if isinstance(inputString, str):
        out = inputString.lower()
        out = re.sub(r'[^a-f0-9]', "" , out)

        if(len(out) == (2*numBytes)):
            return out
        else:
            raise RigError("invalid hex string: " + inputString)
    else:
        return None

def prettyHexString(inBytes,group=2,sep=' '):
    temp = binascii.hexlify(bytes(inBytes)).decode("utf-8").upper()

    #split every N chars with seperator
    out = sep.join(temp[i:i+group] for i in range(0, len(temp), group))
    return out