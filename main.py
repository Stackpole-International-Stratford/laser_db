# import sqlite3
import time
from pylogix import PLC
import re
from datetime import datetime
import sys
import logging
from systemd.journal import JournaldLogHandler
import yaml
import os

import mysql.connector
from mysql.connector import Error

# CHECK_TAG = 'Verify_Barcode'
# CODE_TAG = 'Laser_QR_Code_Text'
# GOOD_TAG = 'Barcode_OK'
# BAD_TAG = 'Barcode_Not_OK'
# LASER_JOB = 'Part_Detected_To_Run'


laser_dict = {}


def setup_logging(log_level=logging.DEBUG):
    logger = logging.getLogger('laserdb')
    journald_handler = JournaldLogHandler()
    journald_handler.setFormatter(
        logging.Formatter('[%(levelname)s] %(message)s'))
    logger.addHandler(journald_handler)
    # handler = logging.StreamHandler(sys.stdout)
    # logger.addHandler(handler)
    logger.setLevel(log_level)
    return logger


def load_PUNS(config):

    # TODO Move params to .env file
    db_params = {'host': '10.4.1.245',
                 'port': 6601,
                 'database': 'django_pms',
                 'user': 'muser',
                 'password': 'wsj.231.kql'}

    connection = mysql.connector.connect(**db_params)
    puns = []
    try:
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            part_mapping = config.get('part_map')
            for key, value in part_mapping.items():

                sql = 'SELECT * FROM barcode_barcodepun '
                sql += f'WHERE part_number = "{value}" '
                sql += f'AND active = true;'

                cursor.execute(sql)
                row = cursor.fetchone()
                if row:
                    pun = {
                        'part': row['part_number'],
                        'regex': row['regex'],
                        'machine_part': key,
                    }
                    puns.append(pun)

    except Error as e:
        print("Error while connecting to MySQL", e)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

    return puns


# New gas parts, old deisel parts
def get_PUNS():
    PUNS = [{'part': '50-8670', 'regex': '^V5SS(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[1,2,3,4])(?P<sequence>\\d{4})24046420$'},
            {'part': '50-5401',
                'regex': '^V3SS(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[1,2,3,4])(?P<sequence>\\d{4})24046418$'},
            {'part': '50-0450',
            'regex': '^V5SS(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[1,2,3,4])(?P<sequence>\\d{4})24280450$'},
            {'part': '50-0447',
            'regex': '^V3SS(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[1,2,3,4])(?P<sequence>\\d{4})24049832$'},
            {'part': '50-5404',
            'regex': '^V6SS(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[1,2,3,4])(?P<sequence>\\d{4})24295404$'},
            {'part': '50-0519',
            'regex': '^V6SS(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[1,2,3,4])(?P<sequence>\\d{4})24280519$'},
            {'part': '50-3214',
            'regex': '^GTALB(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[0,1,2,3]0)(?P<sequence>\\d{4})LC3P 7D007 CB$'},
            {'part': '50-5214',
            'regex': '^GTALB(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[0,1,2,3]0)(?P<sequence>\\d{4})LC3P 7D007 BB$'},
            ]
    return PUNS

# new gas parts, NEW deisel parts


def get_PUNS3():
    PUNS = [{'part': '50-8670', 'regex': '^V5SS(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[1,2,3,4])(?P<sequence>\\d{4})24049840$'},
            {'part': '50-5401',
                'regex': '^V3SS(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[1,2,3,4])(?P<sequence>\\d{4})24049838$'},
            {'part': '50-0450',
            'regex': '^V5SS(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[1,2,3,4])(?P<sequence>\\d{4})24280450$'},
            {'part': '50-0447',
            'regex': '^V3SS(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[1,2,3,4])(?P<sequence>\\d{4})24049832$'},
            {'part': '50-5404',
            'regex': '^V6SS(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[1,2,3,4])(?P<sequence>\\d{4})24049836$'},
            {'part': '50-0519',
            'regex': '^V6SS(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[1,2,3,4])(?P<sequence>\\d{4})24280519$'},
            {'part': '50-3214',
            'regex': '^GTALB(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[0,1,2,3]0)(?P<sequence>\\d{4})LC3P 7D007 CB$'},
            {'part': '50-5214',
            'regex': '^GTALB(?P<year>\\d\\d)(?P<jdate>[0-3]\\d\\d)(?P<station>[0,1,2,3]0)(?P<sequence>\\d{4})LC3P 7D007 BB$'},
            ]
    return PUNS


def config_default(config_dict, key, default):
    if key not in config_dict:
        config_dict[key] = default


def read_config_file(config_key=None):
    if len(sys.argv) == 2:
        config_path = f'./configs/{sys.argv[1]}.yml'
    else:
        config_path = f'/etc/laserdb/{config_key}.config'

    logger.info(f'Reading config from {config_path}')

    if not os.path.exists(config_path):
        logger.error(f'Config file not found! {config_path}')
        raise ValueError(f'Config file not found! {config_path}')

    with open(config_path, 'r') as file:
        config = yaml.load(file, Loader=yaml.FullLoader)

    return config


def startup():
    global logger
    logger = setup_logging(logging.INFO)

    global config
    config = read_config_file("laserdb")
    tags = config.get('tags')
    global CHECK_TAG
    CHECK_TAG = tags.get('CHECK_TAG')
    global CODE_TAG
    CODE_TAG = tags.get('CODE_TAG')
    global GOOD_TAG
    GOOD_TAG = tags.get('GOOD_TAG')
    global BAD_TAG
    BAD_TAG = tags.get('BAD_TAG')
    global LASER_JOB
    LASER_JOB = tags.get('LASER_JOB')

    global PUNS
    PUNS = load_PUNS(config)

    global GRADE_RESULT
    GRADE_RESULT = tags.get('GRADE_RESULT', 'BarcodeResultString')
    global last_grade_result
    last_grade_result = ""

    # global last_jday
    # last_jday = datetime.now().timetuple().tm_yday


def check_barcode(barcode, job):

    # https://stackoverflow.com/a/8653568
    pun_entry = next(
        (item for item in PUNS if item["machine_part"] == f'{job}'), None)
    if not pun_entry:
        logger.error(f'Failed to find part data for {job}!')
        return False

    part = pun_entry.get('part')

    result = re.search(pun_entry['regex'], barcode)
    if not result:
        logger.error(
            f'Failed to match part data! {barcode} {pun_entry["part"]}')
        return False

    current_year = datetime.now().timetuple().tm_year-2000
    year = result.group('year')
    if not int(year) == current_year:
        logger.error(f'Unexpected year, {year}, expected {current_year}!')
        return False

    day_of_year = datetime.now().timetuple().tm_yday
    jdate = result.group('jdate')
    jdate = int(jdate)
    if abs(jdate - day_of_year) > 1:
        logger.error(
            f'Unexpected day of the year, {jdate}, expected: {day_of_year}')
        return False

    station = result.group('station')
    sequence = result.group('sequence')

    tic = time.time()
    connection = mysql.connector.connect(host='10.4.1.245',
                                         port=6601,
                                         database='django_pms',
                                         user='muser',
                                         password='wsj.231.kql')
    try:
        if connection.is_connected():

            sql = 'SELECT COUNT(*) AS count FROM barcode_lasermark '
            sql += f'WHERE part_number = "{pun_entry["part"]}" '
            sql += f'AND bar_code = "{barcode}";'
            cursor = connection.cursor(dictionary=True)
            cursor.execute(sql)
            rows = cursor.fetchall()
            if rows[0]['count'] > 0:
                logger.error(f'Found in db! : {barcode}')
                return False
            else:
                sql = 'INSERT INTO barcode_lasermark (part_number, bar_code, created_at) '
                sql += f'VALUES("{pun_entry["part"]}", "{barcode}", NOW());'
                cursor.execute(sql)
                rows = cursor.fetchall()
                connection.commit()

    except Error as e:
        logger.error(f'MySQL Error: {e}')
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

    toc = time.time()
    logger.info(
        f'Verified: {barcode} against: {part}: {(toc - tic):.4} seconds')
    return True


def write_tag(comm, tag, value=True):
    passes = 0
    rewrite = True
    while rewrite:

        result = comm.Write(tag, value)
        passes += 1
        if result.Status == 'Success':
            check_result = comm.Read(CHECK_TAG)
            tag_result = comm.Read(tag)
            if check_result.Value == False:
                rewrite = False
            if tag_result.Value == True:
                rewrite = False
    logger.debug(f'Wrote tag in {passes} passes')


def update_grade_info(grade_camera_string):
    if grade_camera_string == 'ERROR':
        return
    tic = time.time()
    connection = mysql.connector.connect(host='10.4.1.245',
                                         port=6601,
                                         database='django_pms',
                                         user='muser',
                                         password='wsj.231.kql')
    try:
        if connection.is_connected():

            sql = 'UPDATE barcode_lasermark '
            sql += f'SET grade="{grade_camera_string[-1:]}" '
            sql += f'WHERE bar_code="{grade_camera_string[:-2]}" '
            sql += f'LIMIT 1;'
            # print(sql)

            cursor = connection.cursor()
            cursor.execute(sql)
            connection.commit()

    except Exception as e:
        logger.error(f'Unhandled Exception: {e}')

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

    toc = time.time()
    logger.info(
        f'Updated: {grade_camera_string[:-2]} with grade: {grade_camera_string[-1:]}: {(toc - tic):.4} seconds')


if __name__ == "__main__":
    startup()

    comm = PLC()
    comm.IPAddress = config.get('ip')

    logger.info('Starting main loop')

    while True:
        try:
            result = comm.Read(CHECK_TAG)

            if result.Status == 'Success':
                if result.Value:
                    tags = comm.Read([CODE_TAG, LASER_JOB])
                    mark = tags[0].Value
                    job = tags[1].Value
                    status = check_barcode(mark, job)
                    if status:
                        write_tag(comm, GOOD_TAG)
                    else:
                        write_tag(comm, BAD_TAG)
                    waiting = True
                    while waiting:
                        waiting = comm.Read(CHECK_TAG).Value
                        time.sleep(.1)

                    time.sleep(1)

            else:
                logger.error(f'Failed to read {CHECK_TAG}: {result.Status}')
                time.sleep(2)

            result = comm.Read(GRADE_RESULT)
            if result.Status == 'Success':
                result.Value = result.Value[:result.Value.index('\r')]
                if last_grade_result == '':
                    last_grade_result = result.Value
                if result.Value != last_grade_result:
                    last_grade_result = result.Value
                    # print(f'{result.Value}')
                    update_grade_info(result.Value)

            time.sleep(1)

        except Exception as e:
            logger.error(f'Unhandled Exception: {e}')
