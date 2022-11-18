# import sqlite3
import time
from pylogix import PLC

CHECK_TAG = 'Verify_Barcode'
CODE_TAG = 'Laser_QR_Code_Text'
GOOD_TAG = 'Barcode_OK'
BAD_TAG = 'Barcode_Not_OK'
LASER_JOB = 'Laser_Job_Req_num'

def startup():
    pass


def check_barcode(barcode, part):
    print('Part: ', part ,'Barcode: ', barcode)
    return True


if __name__ == "__main__":
    startup()

    with PLC() as comm:
        comm.IPAddress = '192.168.1.3'
        read = True
        while read:
            try:
                result=comm.Read(CHECK_TAG)
                if result.Value == True:
                    tags = comm.Read([CODE_TAG, LASER_JOB])
                    mark = tags[0].Value
                    job = tags[1].Value
                    status =  check_barcode(mark, job)
                    comm.Write([(GOOD_TAG, status), (BAD_TAG, not status), (CHECK_TAG, False)])
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
