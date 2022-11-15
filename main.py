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
                    status =  check_barcode(CODE_TAG)
                    comm.Write([(GOOD_TAG, status), (BAD_TAG, not status)])
                else:
                    time.sleep(.2)

            except KeyboardInterrupt:
                print('exiting')
                read = False
            except Exception as e:
                print('Unhandled Exception', e)
            

# db = sqlite3.connect('TEST.db')
# cursor = db.cursor()
# print('Connect ok')
