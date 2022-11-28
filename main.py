# import sqlite3
import time
from pylogix import PLC
import re
from datetime import datetime

CHECK_TAG = 'Verify_Barcode'
CODE_TAG = 'Laser_QR_Code_Text'
GOOD_TAG = 'Barcode_OK'
BAD_TAG = 'Barcode_Not_OK'
LASER_JOB = 'Laser_Job_Req_num'

PUNS = [{'part': '50-8670', 'regex':'^V5SS(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[1,2,3,4])(?P<sequence>\\d{4})24046420$'},
        {'part': '50-5401', 'regex': '^V3SS(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[1,2,3,4])(?P<sequence>\\d{4})24046418$'},
        {'part': '50-0450', 'regex': '^V5SS(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[1,2,3,4])(?P<sequence>\\d{4})24280450$'},
        {'part': '50-0447', 'regex': '^V3SS(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[1,2,3,4])(?P<sequence>\\d{4})24280447$'},
        {'part': '50-5404', 'regex': '^V6SS(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[1,2,3,4])(?P<sequence>\\d{4})24295404$'},
        {'part': '50-0519', 'regex': '^V6SS(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[1,2,3,4])(?P<sequence>\\d{4})24280519$'},
        {'part': '50-3214', 'regex': '^GTALB(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[0,1,2,3]0)(?P<sequence>\\d{4})LC3P 7D007 CB$'},
        {'part': '50-5214', 'regex': '^GTALB(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[0,1,2,3]0)(?P<sequence>\\d{4})LC3P 7D007 BB$'},
]

def startup():
    pass


def check_barcode(barcode, part):

    print('Part: ', part ,'Barcode: ', barcode)
    pun_entry = PUNS[part-1]

    result = re.search(pun_entry.get('regex'), barcode)
    if not result:
        return False

    year = result.group('year')
    if not year == '22':
        return False

    day_of_year = datetime.now().timetuple().tm_yday
    jdate = result.group('jdate')
    if not int(jdate) == day_of_year:
        return False
    
    station = result.group('station')
    sequence = result.group('sequence')

    return True


if __name__ == "__main__":
    startup()

    with PLC() as comm:
        comm.IPAddress = '192.168.1.3'
        read = True
        while read:
            try:
                result=comm.Read(CHECK_TAG)
                if result.Value:
                    tags = comm.Read([CODE_TAG, LASER_JOB])
                    mark = tags[0].Value
                    job = tags[1].Value
                    status =  check_barcode(mark, job)
                    comm.Write([(GOOD_TAG, status), (BAD_TAG, not status)])
                    waiting = True
                    while waiting:
                        waiting = comm.Read(CHECK_TAG).Value
                        time.sleep(.2)
                      
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
