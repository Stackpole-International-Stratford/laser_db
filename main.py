# import sqlite3
import time
from pylogix import PLC

CHECK_TAG = ''
CODE_TAG = ''
GOOD_TAG = ''
BAD_TAG = ''

def startup():
    pass


def check_barcode(barcode):
    return True



if __name__ == "__main__":
    with PLC() as comm:
        comm.IPAddress = '192.168.1.1'
        read = True
        while read:
            try:
                if comm.Read(CHECK_TAG):
                    tag = comm.Read(CODE_TAG)
                    if check_barcode(CODE_TAG):
                        comm.Write([(GOOD_TAG, True), (BAD_TAG, False)])
                    else:
                        comm.Write([(GOOD_TAG, False), (BAD_TAG, True)])
                else:
                    time.sleep(.2)
            except:
                pass

        ret = comm.Read('MyTagName')
        print(ret.TagName, ret.Value, ret.Status)

# db = sqlite3.connect('TEST.db')
# cursor = db.cursor()
# print('Connect ok')
