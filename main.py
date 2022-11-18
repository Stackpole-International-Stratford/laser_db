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


def check_barcode(barcode):
    print(barcode)
    return True


if __name__ == "__main__":
    startup()

    with PLC() as comm:
        comm.IPAddress = '192.168.1.1'
        read = True
        while read:
            try:
                if comm.Read(CHECK_TAG).Value:
                    import pdb; pdb.Pdb().set_trace()
                    tags = comm.Read([CODE_TAG, LASER_JOB])
                    mark = tags[0].Value
                    job = tags[1].Value
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
