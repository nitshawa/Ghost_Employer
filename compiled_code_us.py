# !/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import re
import csv
import mysql.connector
import json
import ast
import datetime
from dateutil import parser
import pygsheets
import MySQLdb
import sys
#from datetime import datetime
from dateutil.relativedelta import relativedelta

reload(sys)
sys.setdefaultencoding("utf-8")
cnx = mysql.connector.connect(
    user='root',
    password='xad',
    host='127.0.0.1',
    database='scrapers',
    charset='utf8',
    use_unicode=True
)

cursor = cnx.cursor()

day_list = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
days_hours = {}
stop_words = ['store','pharmacy','operation','investments','mortgage','trust','sales','of','the','for','more','holiday','christmas','parts','service','gym','kids','club','new','year\'s day','staffed','teller','lobby','drive','thru','branch','dining','room','stores','bank','lobby','served ','dine in','dine','vehicle','certified ','produce','deli','bakery','seafood','carryout','delivery','finance','car','parts','used', '!', 'currently', 'temporarily', 'reopening']
# todo, make into ordered dict to ensure the waterfall is adhered to
replacements = {
    'mon': ['monday', 'montag', 'lundi', 'lunes', 'mon-mon', 'mo ', 'mo:'],
    'mon-':['mo-', 'm-'],
    'tue': ['tuesday', 'dienstag', 'mardi', 'martes', 'tues', 'tue-tue', 'tu ', 'tu:'],
    'tue-':['tu-'],
    'wed': ['wednesday', 'mittwoch', 'mercredi', 'mircoles', 'wed-wed', 'wen','we ','we:'],
    'wed-':['we-'],

    'thu': ['thursday', 'donnerstag', 'jeudi', 'jueves', 'thurs', 'thur','thr', 'thu-thu', 'th ','th-', 'th:'],#, 'th'], # 'th' is making sometime breaks the code like in Bonefish,  HEB foods, when day expention is required
    'thu-':['th-'],

    'fri': ['friday', 'freitag', 'vendredi', 'viernes', 'fir','fri-fri',  'fr ', 'fr-',  'fr:'],
    'fri-':['fr-'],

    'sat': ['saturday', 'samstag', 'samedi', 'sabado', 'sat-sat', 'sa ', 'sa-', 'sa:'],
    'sat-':['sa-'],

    'sun': ['sunday', 'sonntag', 'dimanche', 'domingo', 'sun-sun' , 'su ', 'su-', 'su:'],
    'sun-':['su-'],

    # 'am': ['a.m', 'A.M.', 'AM', 'am.', '-am', 'a m', 'a.m.', 'am'],
    # 'pm': ['p.m', 'P.M.', 'PM', 'pm.', '-pm', 'p m', 'p.m.', 'pm'],
    "closed": ["zamkniety", "cerrado", "ferme", "geschlossen"],
    "open": ["otwarty", "abierto", "ouvert", "offen"],
    # ' to ': [' a '],
    'mon-sun ' : ['daily','every day', 'everyday', 'all week', '7 days a week', 'seven days a week', '7 days', 'per day', '7days'],
    '[]': ['closed - closed', 'closed-closed', 'closed:closed', 'close - close', 'close-close', 'closed', 'close'],
    'mon-fri ': ['weekday_hours', 'weekday', 'weekdays', 'mo-fr',  'mon-f ', 'm-f '], #for simmons_bank only one m-f
    ' ': ['_hours', 'hrs', 'black', ' (est)', 'open', '-none'],
    # ', ': ['/'],
    '&': ['\u0026', 'and'],
    'mon-sun : 00:00-00:00':['24/7', 'open 24 hours'],
    '00:00-00:00': ['24 hours','24:00rs', '24:00urs', '24:00urs', '24:00s', '24 hrs', 'all day', 'all:day'],
     '-': [' through ', ' to ', ' thuough ', '\xe2\x80\x93'],
       # '00:00': ['24:00'],
       # '00:30': ['24:30'],
       ' 00:00 ': ['midnight'],
       # '23:59-': ['midnight-']

}

replacement_7days = {'mon-sun : 00:00-00:00':[
'24/7',
'open 24 hours',
'24 Hours Open',
'all day',
'all:day',
'open 24 hours per day may vary',
'open 24 hrs',
'24 hours, 7 days a week',
'24 hours open']}

def remove_html_tags(value):
  tags = re.compile('<.*?>')
  clean_value = re.sub(tags, '', value)
  return clean_value

def replace_24_by_7(value):
    value = value.lower()
    for (key, values) in replacement_7days.iteritems():
        for rep in values:
            if value.strip() == rep: # if days are not given
                try:
                    value = value.replace(rep, key)
                except:
                    continue
    return value


def replace_keywords(value):
    value = remove_html_tags(value)
    value = replace_24_by_7(value)
    value = value.lower()
    for (key, values) in replacements.iteritems():
        for rep in values:
            try:
                value = value.replace(rep, key)
            except:
                continue
    return value

def replace_french_from_to(value):
    x = re.sub(r'du (\w{3}) au (\w{3})', r'\1:\2', value)
    x = re.sub(r'le (\w{3})', r'\1', x)
    return x

def add_trailing_zeros(matchobj):
    time_block = int(matchobj.group(0))
    if time_block < 10:
        time_block = '{0:>02}'.format(str(time_block))
        return '{0:<04}'.format(str(time_block))
    return '{0:<04}'.format(matchobj.group(0))

def replace_hours_without_time_delimeter(value):
    # if any(x not in value for x in ['am', 'pm', 'p', 'a']):
    #     value = re.sub(r'(\d+)', add_trailing_zeros, value)

    return re.sub(r'(\d{1,2})(\d{2})', r'\1:\2', value)


def replace_hour_groups(value):
    p =r'\[(\(\d{2}:\d{2},\d{2}:\d{2}\))\]/\[(\(\d{2}:\d{2},\d{2}:\d{2}\))\]'
    return re.sub(p, r'[\1,\2]', value)

def without_am_pm(matchobj):

    obj = matchobj.groupdict()
    start_hour = int(obj.get('start_hour').strip())
    start_min = int(obj.get('start_min').strip())
    end_min = int(obj.get('end_min').strip())
    end_hour = int(obj.get('end_hour').strip('-'))

    if start_hour > 23:
        start_hour = 00
    if end_hour > 23:
        end_hour = 00

    if start_min > 59:
        start_min = 00

    if end_min > 59:
        end_min = 00

    if  start_hour != 0 and end_hour != 0:
        if end_hour - start_hour <= 3  :
            end_hour = (end_hour + 12) % 24



    return  " {0:02d}:{1:02d}-{2:02d}:{3:02d}".format(start_hour,start_min, end_hour, end_min)


def replace_hours_for_match(matchobj):
    obj = matchobj.groupdict()

    int_hour = 0
    str_hour = obj.get('hour')
    if len(str_hour) > 0:
        int_hour = int(str_hour)

    int_min = 0
    str_min = obj.get('min')
    if len(str_min) > 0:
        int_min = int(str_min)
    ampm = obj.get('ampm', '').replace('.', '').replace(' ', '')
    if ampm in ['p', 'pm']  and  int_hour != 12: # 12pm -> 12
        int_hour = (int_hour + 12) % 24

    if ampm in ['a','am'] and int_hour == 12:  #12am -> 00
        int_hour = (int_hour + 12) % 24

    if int_hour > 23 :
        int_hour = 00

    if int_min > 59:
        int_min = 00
    return "{0:02d}:{1:02d}".format(int_hour, int_min)


def convert_to_24h(value):
    # print value, 'value------'
    pattern =  r"""(?P<hour>\d{1,2})[:hH]{0,1}(?P<min>\d{0,2})[:.hH]{0,1}(?P<sec>\d{0,2})[' ']{0,1}(?P<ampm>a |am|a.m.|am.|a.m|a m|a|p |pm|p.m.|pm.|p.m|p m|p)"""
    raw_convertion = re.sub(pattern, replace_hours_for_match, value)
    print raw_convertion, 'raw--------------'
    # valid_pattern = r"(?P<start>\d{2})(?P<mins>.*?)(?P<end>[-]{2})"
    valid_pattern = r'(?P<start_hour>\d{1,2}):(?P<start_min>\d{2})-(?P<end_hour>\d{1,2}):(?P<end_min>\d{2})'

    valid_convert = re.sub(valid_pattern, without_am_pm, raw_convertion)
    print valid_convert, 'valid_convert--------------'

    return valid_convert


def replace_with_structured_hours(matchobj):
    return "['open': '{0}', 'close': '{1}']".format(matchobj.group(1), matchobj.group(2))


def replace_with_unstructured_hours(matchobj):
    return "[({0},{1})]".format(matchobj.group(1), matchobj.group(2))


def replace_open_close_delimeter(value):
    # pattern = r'(\d{2}:\d{2})[\D]*(\d{2}:\d{2})'
    pattern = r'(\d{1,2}:\d{2}[:\d{2}]*)[\D]*(\d{1,2}:\d{2}[:\d{2}]*)' # for seconds Qdoba
    # pattern = r'(\d{2}:\d{2})[\D]*(\d{2}:\d{2})'
    # pattern = r'(\d{2}:\d{2})[\s-]*(\d{2}:\d{2})'
    return re.sub(pattern, replace_with_unstructured_hours, value)


def time_day_dict(value):
    days_hours = {}
    pattern = "(\[.*?\])"
    hours = re.findall(pattern, value)
    indexer = 0

    for  hour in hours:
        start = value.find("]", indexer) + 1
        end = value.find("[", start)
        if end == -1: # to get last dayname
            end = len(value)
        raw_days = value[start:end]
        days = ' '.join(raw_days.replace('(', '').replace(')','').replace(',', '').replace('.', '').replace(':','').split()).strip('-').strip()
        days_hours[days] = hour
        indexer = start
    return days_hours

def string_to_dict(value):
    """
        input string must have a format as
        mon: [(08:45,19:30)], tue: [(08:45,19:30)], wed: [(08:45,19:30)], thu: [(08:45,19:30)], fri: [(08:45,20:00)], sat: [(08:45,19:30)]
        mon. & thu. [(10:00,20:00)],tue., wed., fri. [(10:00,17:30)],sat. [(10:00,17:30)],sun. [(24:00,17:00)]
    """
    days_hours = {}
    pattern = "(\[.*?\])"
    hours = re.findall(pattern, value)
    indexer = 0
    if value.find("[") == 0:
      return time_day_dict(value)


    for hour in hours:
        start = value.find("[" ,indexer)
        end = value.find(']', start) + 1
        raw_days = re.findall(r'^(.*?)\[', value[indexer: end])[0]
        # need to clean day names before this point
        days = ' '.join(raw_days.replace(',', '').replace('.', '').replace(':','').split()).strip('-').strip()
        days_hours[days] = hour
        indexer = end
    return days_hours


def day_expand(days_hours):
    """
    Input must be dict.
    -- Must have a "-" (hyphen) as separator or day's keys have start and end eg. mon - thru etc...
        -- In this case function would return the expanded dict with 7 days.
            If any day is missing then only it will put value as blank list.
    -- if multiple days comes with out separator eg.. tue, wed, thru... etc..
        -- Function would return multiple days with same hours
            eg.. tue : [00:23:59], wed : [00:23:59], thru : [00:23:59]
    unhandled cases:
        if both separator and multiple days key appears : eg..
        mon-fri, sat: 9:00 am - 8:00 pm
        mon-tue-wed-fri 8.30am-6.30pm , thur 8.30am-5.30pm , sat 9am-12noon , sun closed

    """

    days_hours_copy = {k: v for k, v in days_hours.iteritems() if v}
    days = [x for x in days_hours.keys()]
    for day, hours in days_hours_copy.iteritems():
        if '-' in day:

            """if dash separator given in keys"""
            del days_hours[day]

            start_day_index, end_day_index = [day_list.index(x.strip(' /,')) for x in day.split('-')]

            if end_day_index <= start_day_index:
                expanded_days = day_list[start_day_index:] + day_list[:end_day_index + 1]
                for expanded_day in expanded_days:
                    days_hours[expanded_day] = hours
            else:
                expanded_days = day_list[start_day_index:end_day_index + 1]
                for expanded_day in expanded_days:
                    days_hours[expanded_day] = hours

        else:
            """check if multiple days given without separator"""
            multiple_days = re.findall(r'(\w{3})', day)
            if len(multiple_days) > 0:
                del days_hours[day]
                for multiple_day in multiple_days:
                    days_hours[multiple_day] = hours

    '''updating dict with missing day as blank'''
    for day in day_list:
        if day not in days_hours.keys():
            days_hours[day] = []

    if  sorted(days_hours.keys()) == sorted(day_list) :
        return days_hours
    else:
        # for k, v in days_hours.iteritems():
        #     if k not in day_list:
        #         k = 'unknown day'
        return 'Invalid day name -> {}'.format(days_hours)

def sorted_output(value):

    """Temporay function to check output in sorted format"""
    output = []
    for i in day_list:
        # print value
        output.append("{0}:{1}".format(i,value[i]))
    return '{ ' + ', '.join(output) + ' }'

def validate_input_string(value):
    checked = []
    for bad_word in stop_words:
        if bad_word in value:
            checked.append(bad_word)
    length_bad_words = len(checked)
    if length_bad_words > 0:
        return 'found invalid words > {}'.format(', '.join(checked))
    else:
        return True

def replace_relative_days(value):
    min_index = float("inf")
    for day in day_list:
        day_index = value.find(day)
        # print day_index, '---------'
        if day_index < min_index and day_index != -1:
            min_index = day_index
            # print day_index

    start_day = value[min_index: min_index+3]
    start_day_index = day_list.index(start_day)

    if 'tomorrow' in value:
        relative_days_assigned = value.replace('tomorrow', day_list[start_day_index-1]).replace('today', day_list[start_day_index-2])
    else:
        relative_days_assigned = value.replace('today', day_list[start_day_index-1])
    print relative_days_assigned
    return relative_days_assigned

def date_to_week_day(value):
    try:
        formated_date = parser.parse(value).strftime('%Y-%m-%d')

        return datetime.datetime.strptime(formated_date, '%Y-%m-%d').strftime('%A')
    except:
        raise
        return 'invalid date format!:{}'.format(value)
# print date_to_week_day(string)
# date = 'January 11, 2010'

def formated_date(matchobj):
    return date_to_week_day(matchobj.group())


def check_string_for_date(value):
    pattern = r'(?P<year>(?:19|20)\d\d)[- /.](?P<month>0[1-9]|1[012])[- /.](?P<date>0[1-9]|[12][0-9]|3[01])'
    value = re.sub(pattern, formated_date, value)
    return value



def debug_formated_output_dict(value):
    print value
    print '-'*100
    formated_output = {}
    for key, val in value.iteritems():

        if isinstance(val, unicode):

            value = re.sub(r'(\d{2}:\d{2}[:\d{2}]*),(\d{2}:\d{2}[:\d{2}]*)', r"'\1','\2'", val)
            value = ast.literal_eval(value)

            formated_output[key] = value
        else:
             formated_output[key] = val

    print 'formated_output', formated_output
    print
    return formated_output

def formated_output_dict(value):
    final_output = []
    unique = set([x for x in value.values() if type(x) is not list ])
    formated_output = {}
    for unique_val in unique:
        shared_keys = []

        for key, val in value.iteritems():
            if value[key] == unique_val:

                shared_keys.append(key)
        formated_output[unique_val] = shared_keys


    for key, val in formated_output.iteritems():

        time_blocks = re.findall(r'\(.*?\)', key)
        for time_block in time_blocks:
            combined_days = {}
            start_time = re.search(r'\((\d{2}:\d{2}[:\d{2}]*)\,', time_block).group(1)
            end_time = re.search(r',(\d{2}:\d{2}[:\d{2}]*)\)', time_block).group(1)
            # combined_days['start_time'] ='{}:00'.format(start_time)
            # combined_days['end_time'] = '{}:00'.format(end_time)
            # combined_days['days'] = val
            start_time = re.search(r'\((\d{2}:\d{2}[:\d{2}]*)\,', time_block).group(1)
            end_time = re.search(r',(\d{2}:\d{2}[:\d{2}]*)\)', time_block).group(1)
            if len(start_time) == 5: #if seconds are not available
                combined_days['start_time'] ='{}:00'.format(start_time)
            else:
                combined_days['start_time'] ='{}'.format(start_time)
            if len(end_time) == 5:
                combined_days['end_time'] = '{}:00'.format(end_time)
            else:
                combined_days['end_time'] = '{}'.format(end_time)
            combined_days['days'] = val
            final_output.append(combined_days)
            combined_days_sorted = combined_days['days'].sort(key=lambda x: day_list.index(x))


    if len(final_output) == 0:
        return []
    return final_output

def update_gsheet(brand_name, sheet_link):
    sheet_key = re.findall(r'\/d\/(.*?)\/edit', sheet_link)[0]
    gc = pygsheets.authorize()

    sht1 = gc.open_by_key(sheet_key)
    wks1 = sht1.worksheet_by_title("validated")
    wks1.export(pygsheets.ExportType.CSV, brand_name + '.csv')

    output_csv = csv.writer(open( "/media/nitin/809E47539E4740C0/HD/TestCodes/hours_of_operation/testing/compiled_code_us/shared_brands/done_" +brand_name + '.csv', 'wb'))
    output_csv.writerow(["brand_name", "store_name", "type", "address_1",
        "city", "state", "zipcode", "country_code", "phone_number",
         "primary_sic", "secondary_sic", "latitude", "longitude",
         "raw_business_hours", "debug_formated_business_hours","converted_business_hours", "brand_id", "raw_address", "updated_date", "url"])

    input_csv = csv.reader(open(brand_name + '.csv', 'rb'))
    cursor_list = [x for x in input_csv][1:]
    for value in cursor_list:

        brand_name = value[0]
        store_name = value[1]
        store_type = value[2]
        address_1 = value[3]
        city = value[4]
        state = value[5]
        zipcode = value[6]
        country_code = value[7]
        phone_number = value[8]
        primary_sic = value[9]
        secondary_sic = value[10]
        latitude = value[11]
        longitude = value[12]
        raw_business_hours = value[13]
        print
        print 'raw_business_hours', raw_business_hours
        print '.+'*100
        brand_id = value[14]
        raw_address = value[15]
        updated_date = value[16]
        url = value[17]

        value = raw_business_hours
        if value is None:
            continue
        # value = value[13]  # Access tuple from dataset
        # value = value  # from cursor list
        # print value
        if not isinstance(value, str) and not isinstance(value, unicode):
            continue

        value = value.replace("\n", " ").replace("\\n", " ").strip().lower()

        # if value is "":
        #     continue

        validated_check = validate_input_string(value)

        if validated_check is isinstance(validated_check, bool):
            try:
                y = check_string_for_date(value)
                print 'befor replace_keywords', y
                y = replace_keywords(y)
                print 'after replace_keywords', y
                # y = replace_french_from_to(y)
                if 'today' in y:
                    y = replace_relative_days(y)

                y = replace_hours_without_time_delimeter(y)
                # print y, 'replace_hours_without_time_delimeter'
                y = convert_to_24h(y)
                # print y, 'convert_to_24h'

                y = replace_open_close_delimeter(y)
                # print y, 'replace_open_close_delimeter'
                y = replace_hour_groups(y)
                # print y, 'replace_hour_groups'
                not_matched = replace_hour_groups(y)
                y = string_to_dict(y)

                if isinstance(y, dict):
                    try:
                        print 'before day expantion : ', y

                        y = day_expand(y)
                        # y = sorted_output(y)
                        print 'after day expantion : ', y
                        debug_y = debug_formated_output_dict(y)
                        print 'after debug_formated_output_dict : ', debug_y
                        y = formated_output_dict(y)
                        print 'after formated_output_dict : ', y

                    except:
                        raise
                        y = 'Unhandled Day expantion Failed : {0}'.format(y)
                else:
                        y = 'Unhandled Unable to convert in dict : {0}'.format(y)
            except Exception as e:
                raise
                # print e, value
                y = 'Unhandled formats : {0}'.format(value)
                pass
        else:
            print 'in else ...................', validated_check
            y = validated_check
            debug_y = y
            not_matched = replace_hour_groups(y)

        # print y

        formated_business_hours = y
        debug_formated_business_hours = debug_y
        if value == '':

            formated_business_hours = ''
        # break

        # output_csv.writerow([' '.join(value.split()).encode('ascii', 'ignore'), y, ' '.join(not_matched.split())])
        output_csv.writerow([brand_name, store_name, store_type, address_1, city, state, zipcode, country_code, phone_number, primary_sic, secondary_sic, latitude, longitude, raw_business_hours, debug_formated_business_hours, formated_business_hours, brand_id, raw_address, updated_date, url])



def main_test():
    # query =  """
    #             SELECT raw_business_hours FROM O_O_DATA.scrapers_hoo;
    #                """
    # cursor.execute(query)
    # # input_all_brands_list = [x for x in cursor.fetchall()]
    # # for row in input_all_brands_list:
    # #     brand_name = row[0]
    # #     print brand_name
    #from validated database
    brand_name = 'Walmart'
    query = """
       SELECT * FROM O_O_DATA.scrapers_hoo
       WHERE brand_name LIKE \"%"""+ brand_name + """%\";
        """
    # # and raw_business_hours like "%24:00-18:00%" limit 2
    # # # #    #AND country_code = "US";
    # # # # # print query
    # # # # # exit()
    cursor.execute(query)

    output_csv = csv.writer(open( "/media/nitin/809E47539E4740C0/HD/TestCodes/hours_of_operation/testing/compiled_code_us/attemp2/" + brand_name + ' store_hours.csv', 'wb'))
    # output_csv.writerow(['input_string', 'output_dict', "unmatched"])
    output_csv.writerow(["brand_name", "store_name", "type", "address_1",
        "city", "state", "zipcode", "country_code", "phone_number",
         "primary_sic", "secondary_sic", "latitude", "longitude",
         "raw_business_hours", "debug_formated_business_hours","converted_business_hours", "brand_id", "raw_address", "updated_date", "url"])

    # from convert sheets
    # input_csv = csv.reader(open('/home/nitin/Downloads/Acura_US - Validated 2017-11.csv', 'rb'))
    # cursor_list = [
    # 'today: 6:00 am - 11:00 pm/ 6:00 am - 11:00 pm, tomorrow: 6:00 am - 11:00 pm thursday: 6:00 am - 11:00 pm friday: 6:00 am - 11:00 pm saturday: 6:00 am - 11:00 pm sunday: 6:00 am - 11:00 pm monday: 6:00 am - 11:00 pm']
    # # 'mon-06:00:24:00 tue-06:00:24:00 wed-06:00:24:00 thr-06:00:24:00 fri-06:00:24:00 sat-06:00:24:00 sun-06:00:24:00']
    # cursor_list = [x for x in input_csv][1:]

    # for value in cursor_list:
    for value in cursor:

        brand_name = value[0]
        store_name = value[1]
        store_type = value[2]
        address_1 = value[3]
        city = value[4]
        state = value[5]
        zipcode = value[6]
        country_code = value[7]
        phone_number = value[8]
        primary_sic = value[9]
        secondary_sic = value[10]
        latitude = value[11]
        longitude = value[12]
        raw_business_hours = value[13]
        print
        print 'raw_business_hours', raw_business_hours
        print '.+'*100
        # formated_business_hours = y
        brand_id = value[14]
        raw_address = value[15]
        updated_date = value[16]
        url = value[17]
        #for csv_indexes
        # brand_id = value[15]
        # raw_address = value[16]
        # updated_date = value[17]
        # url = value[18]
        if value is None:
            continue
        # value = value[13]  # Access tuple from dataset
        value = raw_business_hours
        # value = value  # from cursor list
        # print value
        if not isinstance(value, str) and not isinstance(value, unicode):
            continue

        value = value.replace("\n", " ").replace("\\n", " ").strip().lower()

        if value is "":
            continue

        validated_check = validate_input_string(value)

        if validated_check is isinstance(validated_check, bool):
            try:
                y = check_string_for_date(value)
                print 'befor replace_keywords', y
                y = replace_keywords(y)
                print 'after replace_keywords', y
                # y = replace_french_from_to(y)
                if 'today' in y:
                    y = replace_relative_days(y)

                y = replace_hours_without_time_delimeter(y)
                # print y, 'replace_hours_without_time_delimeter'
                y = convert_to_24h(y)
                # print y, 'convert_to_24h'

                y = replace_open_close_delimeter(y)
                # print y, 'replace_open_close_delimeter'
                y = replace_hour_groups(y)
                # print y, 'replace_hour_groups'
                not_matched = replace_hour_groups(y)
                y = string_to_dict(y)

                if isinstance(y, dict):
                    try:
                        print 'before day expantion : ', y

                        y = day_expand(y)
                        # y = sorted_output(y)
                        print 'after day expantion : ', y
                        debug_y = debug_formated_output_dict(y)
                        print 'after debug_formated_output_dict : ', debug_y
                        y = formated_output_dict(y)
                        print 'after formated_output_dict : ', y

                    except:
                        raise
                        y = 'Unhandled Day expantion Failed : {0}'.format(y)
                else:
                        y = 'Unhandled Unable to convert in dict : {0}'.format(y)
            except Exception as e:
                raise
                # print e, value
                y = 'Unhandled formats : {0}'.format(value)
                pass
        else:
            y = validated_check
            debug_y = y
            not_matched = replace_hour_groups(y)
        # print y
        formated_business_hours = y
        debug_formated_business_hours = debug_y
        # break

        # output_csv.writerow([' '.join(value.split()).encode('ascii', 'ignore'), y, ' '.join(not_matched.split())])
        output_csv.writerow([brand_name, store_name, store_type, address_1, city, state, zipcode, country_code, phone_number, primary_sic, secondary_sic, latitude, longitude, raw_business_hours, debug_formated_business_hours, formated_business_hours, brand_id, raw_address, updated_date, url])
        # break
def accuracy_csv():
        accuracy_csv = csv.reader(open("total_with_bad_updated"+ ' store_hours.csv', 'rb'))
        accuracy_csv = filter(None,[x for x in accuracy_csv][1:])

        total  = len([x for x in accuracy_csv])
        print ("Total rows %d" % total)

        unhandled = len([x for x in accuracy_csv if  'Unhandled' in x[1]  and 'invalid' in x[1] ])
        per_accuracy = ((total - unhandled) * 100)/total
        # print per_accuracy
        print ("Unhandled %d" % unhandled)
        print ("Accuracy  %d" % per_accuracy)


        unhandled_csv = csv.writer(open('updated_bad_unhandled_store_hours.csv', 'wb'))
        unhandled_csv.writerow(['input_string', 'output_dict', "unmatched"])
        for row in accuracy_csv:
            if 'Unhandled' in row[1]:
                unhandled_csv.writerow(row)

if __name__ == "__main__":
    # all_brands_output = csv.writer(open('all_brands_output.csv', 'wb'))
    # all_brands_output.writerow(['brand_name', 'accuracy %'])
    # query = """
    #    SELECT brand_name FROM O_O_DATA.scrapers_hoo
    #    group by brand_name;
    #    """
    brand_name = "Petco"
    sheet_link = 'https://docs.google.com/spreadsheets/d/1oYGE0TtgAXE-q-gqoPOjzwbNrxzY0nT-t4JouUBmQu8/edit#gid=1220485708'

    update_gsheet(brand_name, sheet_link)
    # main_test()
    # accuracy_csv()

    # query =
        # Accuracy csv writing

        # all_brands_output.writerow([brand_name, per_accuracy])
        # # break


cursor.close()
cnx.close()
