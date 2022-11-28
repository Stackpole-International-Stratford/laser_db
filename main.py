# import sqlite3
import time
from pylogix import PLC

CHECK_TAG = 'Verify_Barcode'
CODE_TAG = 'Laser_QR_Code_Text'
GOOD_TAG = 'Barcode_OK'
BAD_TAG = 'Barcode_Not_OK'
LASER_JOB = 'Part_Detected_To_Run'

def startup():
    
    pass


def check_barcode(barcode, part):
    print('Part: ', part ,'Barcode: ', barcode)
    return True


def write(comm, tag, value=True):
    passes =0
    rewrite = True
    while rewrite:

        result = comm.Write(tag, value)
        time.sleep(.01)
        passes += 1
        if result.Status =='Success':
            check_result=comm.Read(CHECK_TAG)
            tag_result=comm.Read(tag)
            if check_result.Value == False:
                rewrite = False
            if tag_result.Value == True:
                rewrite = False
    
    print('Write Passes: ', passes)


if __name__ == "__main__":
    startup()

    comm = PLC
    comm.IPAddress = '192.168.1.3'
    read = True
    while True:
        try:
            result=comm.Read(CHECK_TAG)
            if result.Status == 'Success' and result.Value:
                tags = comm.Read([CODE_TAG, LASER_JOB])
                mark = tags[0].Value
                job = tags[1].Value
                status =  check_barcode(mark, job)
                if status:
                    write(comm, GOOD_TAG)
                else:
                    write(comm, BAD_TAG)
                while waiting:
                    waiting = comm.Read(CHECK_TAG).Value
                    time.sleep(.1)
                      
        except KeyboardInterrupt:
            print('exiting')
            read = False
        except Exception as e:
            print('Unhandled Exception', e)
            

# db = sqlite3.connect('TEST.db')
# cursor = db.cursor()
# print('Connect ok')
