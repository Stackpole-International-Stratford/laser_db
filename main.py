# import sqlite3
import time
from pylogix import PLC
import re
from datetime import datetime

import logging
from systemd.journal import JournaldLogHandler



CHECK_TAG = 'Verify_Barcode'
CODE_TAG = 'Laser_QR_Code_Text'
GOOD_TAG = 'Barcode_OK'
BAD_TAG = 'Barcode_Not_OK'
LASER_JOB = 'Part_Detected_To_Run'

PUNS = [{'part': '50-8670', 'regex':'^V5SS(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[1,2,3,4])(?P<sequence>\\d{4})24046420$'},
        {'part': '50-5401', 'regex': '^V3SS(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[1,2,3,4])(?P<sequence>\\d{4})24046418$'},
        {'part': '50-0450', 'regex': '^V5SS(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[1,2,3,4])(?P<sequence>\\d{4})24280450$'},
        {'part': '50-0447', 'regex': '^V3SS(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[1,2,3,4])(?P<sequence>\\d{4})24049832$'},
        {'part': '50-5404', 'regex': '^V6SS(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[1,2,3,4])(?P<sequence>\\d{4})24295404$'},
        {'part': '50-0519', 'regex': '^V6SS(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[1,2,3,4])(?P<sequence>\\d{4})24280519$'},
        {'part': '50-3214', 'regex': '^GTALB(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[0,1,2,3]0)(?P<sequence>\\d{4})LC3P 7D007 CB$'},
        {'part': '50-5214', 'regex': '^GTALB(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[0,1,2,3]0)(?P<sequence>\\d{4})LC3P 7D007 BB$'},
]
  #'V5SS 22 332 3 0002 24049840'

def setup_logging(log_level=logging.DEBUG):
    logger = logging.getLogger('laserdb')
    journald_handler = JournaldLogHandler()
    journald_handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
    logger.addHandler(journald_handler)
    logger.setLevel(log_level)
    return logger

def startup():
    global logger
    logger = setup_logging()
    pass

def check_barcode(barcode, part):

    logger.info('Checking: ', barcode, 'for part: ', part)

    # https://stackoverflow.com/a/8653568
    pun_entry = next((item for item in PUNS if item["part"] == part), None)
    if not pun_entry:
        logger.info('Failed to find part data!')
        return False
    
    result = re.search(pun_entry['regex'], barcode)
    if not result:
        logger.info('Failed to match part data!')
        return False

    year = result.group('year')
    if not year == '22':
        logger.info('Unexpected year, ', year, ' expected 22!')
        return False

    day_of_year = datetime.now().timetuple().tm_yday
    jdate = result.group('jdate')
    if not int(jdate) == day_of_year:
        logger.info('Unexpected day of the year, ', jdate, ' expected: ', day_of_year)
        return False
    
    station = result.group('station')
    sequence = result.group('sequence')

    return True


def write_tag(comm, tag, value=True):
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
    
    logger.info('Write Passes: ', passes)


if __name__ == "__main__":
    startup()

    comm = PLC()
    comm.IPAddress = '192.168.1.3'
    read = True
    logger.info('Starting main loop')
    while True:
        try:
            result=comm.Read(CHECK_TAG)
            if result.Status == 'Success' and result.Value:
                tags = comm.Read([CODE_TAG, LASER_JOB])
                mark = tags[0].Value
                job = tags[1].Value
                status =  check_barcode(mark, job)
                if status:
                    write_tag(comm, GOOD_TAG)
                else:
                    write_tag(comm, BAD_TAG)
                waiting = True
                while waiting:
                    waiting = comm.Read(CHECK_TAG).Value
                    time.sleep(.1)
            else:
                time.sleep(.2)


            print('exiting')
            read = False
        except Exception as e:
            ('Unhandled Exception', e)
    
            

# db = sqlite3.connect('TEST.db')
# cursor = db.cursor()
# print('Connect ok')
