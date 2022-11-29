# import sqlite3
import time
from pylogix import PLC
import re
from datetime import datetime
import sys
import logging
from systemd.journal import JournaldLogHandler

import mysql.connector
from mysql.connector import Error

CHECK_TAG = 'Verify_Barcode'
CODE_TAG = 'Laser_QR_Code_Text'
GOOD_TAG = 'Barcode_OK'
BAD_TAG = 'Barcode_Not_OK'
LASER_JOB = 'Part_Detected_To_Run'


def setup_logging(log_level=logging.DEBUG):
    logger = logging.getLogger('laserdb')
    journald_handler = JournaldLogHandler()
    journald_handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
    logger.addHandler(journald_handler)
    # handler = logging.StreamHandler(sys.stdout)
    # logger.addHandler(handler)
    logger.setLevel(log_level)
    return logger

def get_PUNS2():
    PUNS = []
    try:
        connection = mysql.connector.connect(host='10.4.1.245',
                                            port=6601,
                                            database='django_pms',
                                            user='muser',
                                            password='wsj.231.kql')
        if connection.is_connected():
            # db_Info = connection.get_server_info()
            # print("Connected to MySQL Server version ", db_Info)
            # cursor = connection.cursor()
            # cursor.execute("select database();")
            # record = cursor.fetchone()
            # print("You're connected to database: ", record)

            sql = 'SELECT * FROM barcode_barcodepun '
            sql += f'WHERE active = true;'

            cursor = connection.cursor(dictionary=True)
            cursor.execute(sql)
            rows = cursor.fetchall()
            PUNS = []
            for row in rows:
                pun = {
                    'part': row['part_number'],
                    'regex': row['regex']
                }
                PUNS.append(pun)
            

    except Error as e:
        print("Error while connecting to MySQL", e)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed")    

    return PUNS



def get_PUNS():
    PUNS = [{'part': '50-8670', 'regex':'^V5SS(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[1,2,3,4])(?P<sequence>\\d{4})24046420$'},
        {'part': '50-5401', 'regex': '^V3SS(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[1,2,3,4])(?P<sequence>\\d{4})24046418$'},
        {'part': '50-0450', 'regex': '^V5SS(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[1,2,3,4])(?P<sequence>\\d{4})24280450$'},
        {'part': '50-0447', 'regex': '^V3SS(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[1,2,3,4])(?P<sequence>\\d{4})24049832$'},
        {'part': '50-5404', 'regex': '^V6SS(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[1,2,3,4])(?P<sequence>\\d{4})24295404$'},
        {'part': '50-0519', 'regex': '^V6SS(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[1,2,3,4])(?P<sequence>\\d{4})24280519$'},
        {'part': '50-3214', 'regex': '^GTALB(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[0,1,2,3]0)(?P<sequence>\\d{4})LC3P 7D007 CB$'},
        {'part': '50-5214', 'regex': '^GTALB(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[0,1,2,3]0)(?P<sequence>\\d{4})LC3P 7D007 BB$'},
    ]
    return PUNS


def startup():
    global logger
    logger = setup_logging()

    # Get the current PUNS from the database:
    global PUNS
    PUNS = get_PUNS2()
    PUNS = get_PUNS()


def check_barcode(barcode, part):

    logger.info(f'Checking: {barcode} for part: {part}')
    #return False
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
        logger.info(f'Unexpected year, {year}, expected 22!')
        return False

    day_of_year = datetime.now().timetuple().tm_yday
    jdate = result.group('jdate')
    if not int(jdate) == day_of_year:
        logger.info(f'Unexpected day of the year, {jdate}, expected: {day_of_year}')
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
    
    logger.info(f'Write Passes: {passes}')


if __name__ == "__main__":
    startup()

    comm = PLC()
    comm.IPAddress = '192.168.1.3'
    read = True
    logger.info('Starting main loop')
    while True:
        try:
            # logger.info(f'Reading {CHECK_TAG}')
            result=comm.Read(CHECK_TAG)
            # logger.info(f'{result.TagName}, {result.Status}, {result.Value}')
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

        except Exception as e:
            logger.error(f'Unhandled Exception: {e}')
    
            

# db = sqlite3.connect('TEST.db')
# cursor = db.cursor()
# print('Connect ok')
