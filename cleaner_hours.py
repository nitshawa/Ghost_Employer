#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import unittest
import re
from collections import OrderedDict
# cnx = mysql.connector.connect(
#     user='root',
#     password='xad',
#     host='127.0.0.1',
#     database='scrapers',
#     charset='utf8',
#     use_unicode=True
# )

# cursor = cnx.cursor()

day_list = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun' ]
days_hours = {}

replacements = {
    'mon': ['monday', 'montag', 'lundi', 'lunes', 'mon-mon', 'mo ','mo-', 'mo:'],#, 'm-'],
    'tue': ['tuesday', 'dienstag', 'mardi', 'martes', 'tues', 'tue-tue', 'tu ','tu-', 'tu:'],#, 't-'],
    'wed': ['wednesday', 'mittwoch', 'mercredi', 'miércoles', 'wed-wed', 'wen','we ','we-','we:'],#, 'w-'],
    'thu': ['thursday', 'donnerstag', 'jeudi', 'jueves', 'thurs', 'thur','thr', 'thu-thu', 'th ','th-', 'th:', 'th-'],
    'fri': ['friday', 'freitag', 'vendredi', 'viernes', 'fir', 'fri-fri',  'fr ', 'fr-',  'fr:'],
    'sat': ['saturday', 'samstag', 'samedi', 'sábado', 'sat-sat', 'sa ', 'sa-', 'sa:'],
    'sun': ['sunday', 'sonntag', 'dimanche', 'domingo', 'sun-sun' , 'su ', 'su-', 'su:'],
    # 'am': ['a.m', 'A.M.', 'AM', 'am.', '-am', 'a m', 'a.m.', 'am'],
    # 'pm': ['p.m', 'P.M.', 'PM', 'pm.', '-pm', 'p m', 'p.m.', 'pm'],
    "closed": ["zamknięty", "cerrado", "fermé", "geschlossen"],
    "open": ["otwarty", "abierto", "ouvert", "offen"],
    "mon-fri": ['mo-fr'],
    ' to ': [' à '],
    'mon-sun' : ['daily','every day', 'everyday', 'all week', '7 days a week', 'seven days a week', '7 days', 'per day'],
    '[]': ['closed - closed', 'closed-closed', 'close - close', 'close-close', 'closed', 'close'],
    'mon-fri': ['weekday_hours', 'weekday', 'weekdays'],
    ' ': ['_hours', 'hrs', 'black', ' (est)', 'open'],
    ', ': ['/'],
    '&': ['\u0026'],
    'mon-sun : 00:00-00:00':['24/7'],
    '00:00-00:00': ['24 hours','24:00rs', '24:00urs', '24:00urs', '24:00s', '24 hrs'],
     '-': ['through', 'to', 'thuough', '\xe2\x80\x93', ' – '],
       # '00:00': ['24:00'],
       # '00:30': ['24:30'],
       '-23:59': ['-midnight', ' - midnight'],
       # '23:59-': ['midnight-']

}


def remove_html_tags(value):
  tags = re.compile('<.*?>')
  clean_value = re.sub(tags, '', value)
  return clean_value


def replace_keywords(value):
    value = value.lower()
    for (key, values) in replacements.iteritems():
        for rep in values:
            value = value.replace(rep, key)
    return value



def replace_hours_without_time_delimeter(value):
    return re.sub(r'(\d{1,2})(\d{2})', r'\1:\2', value)


def replace_hour_groups(value):
    p = r'\[(\(\d{2}:\d{2},\d{2}:\d{2}\))\]/\[(\(\d{2}:\d{2},\d{2}:\d{2}\))\]'
    return re.sub(p, r'[\1,\2]', value)


def without_am_pm(matchobj):
    obj = matchobj.groupdict()
    mins = str(obj.get('mins'))
    start_hour = int(obj.get('start').strip())
    end_hour = int(obj.get('end').strip('-'))
    if end_hour - start_hour <3 :
        end_hour = (end_hour + 12) % 24
    return  " {0:02d}{1:s}-{2:02d}".format(start_hour, mins,end_hour)

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

    ampm = obj.get('ampm', '')
    if ampm == 'pm':
        int_hour = (int_hour + 12) % 24

    if ampm == 'am' and int_hour == 12:  #12am -> 00
        int_hour = (int_hour + 12) % 24

    if int_hour > 23:
        int_hour = 00

    if int_min > 59:
        int_min = 00
    return "{0:02d}:{1:02d}".format(int_hour, int_min)


# def convert_to_24h(value):
#     pattern = r"(?P<hour>\d{1,2})[:hH]{0,1}(?P<min>\d{0,2})[:hH]{0,1}(?P<sec>\d{0,2})[' ']{0,1}(?P<ampm>\w{0,2})"
#     return re.sub(pattern, replace_hours_for_match, value)
def convert_to_24h(value):
    pattern =  r"""(?P<hour>\d{1,2})[:hH]{0,1}(?P<min>\d{0,2})[:.hH]{0,1}(?P<sec>\d{0,2})[' ']{0,1}(?P<ampm>am|a.m.|am.|a.m|a m|a|pm|p.m.|pm.|p.m|p m|p)"""
    raw_convertion = re.sub(pattern, replace_hours_for_match, value)
    print raw_convertion, 'raw_conversion'
    valid_pattern = r"(?P<start>\s\d{2})(?P<mins>.*?)(?P<end>[-]\d{2})"
    valid_convert = re.sub(valid_pattern, without_am_pm, raw_convertion)
    return valid_convert


def replace_with_structured_hours(matchobj):
    # print "['open': '{0}', 'close': '{1}']".format(matchobj.group(1), matchobj.group(2)),  '--------------replace_with_structured_hours'
    return "['open': '{0}', 'close': '{1}']".format(matchobj.group(1), matchobj.group(2))

def replace_with_unstructured_hours(matchobj):
    # print  "[({0},{1})]".format(matchobj.group(1), matchobj.group(2)), '---------replace_with_unstructured_hours'
    return "[({0},{1})]".format(matchobj.group(1), matchobj.group(2))


def replace_open_close_delimeter(value):
    pattern = r'(\d{2}:\d{2})[\D]*(\d{2}:\d{2})'
    # pattern = r'(\d{2}:\d{2})[\W{1,2}]*(\d{2}:\d{2})'
    # print re.sub(pattern, replace_with_unstructured_hours, value), '-------replace_open_close_delimeter'
    return re.sub(pattern, replace_with_unstructured_hours, value)

# old logic
# def time_day_dict(value):
#     days_hours = {}
#     pattern = "(\[.*?\])"
#     hours = re.findall(pattern, value)
#     indexer = 0

#     for  hour in hours:
#         start = value.find("]", indexer) + 1
#         end = value.find("[", start)
#         raw_days = value[start:end]
#         days = ' '.join(raw_days.replace('(', '').replace(')','').replace(',', '').replace('.', '').replace(':','').split()).strip('-').strip()
#         days_hours[days] = hour
#         indexer = start
#     return days_hours

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


# old dict
# def string_to_dict(value):
#     """ input string should be like
#     mon - fri: [(09:00,17:30)],sat: [(09:00,13:00)],sun: closed
#     mon [(00:00,23:59)],tue [(00:00,23:59)],wed [(00:00,23:59)],thu [(00:00,23:59)],fri [(00:00,23:59)],sat [(00:00,23:59)],sun [(00:00,23:59)
#     mon. & thu. 10:00 am - 8:00 pm,tue., wed., fri. 10:00 am - 5:30 pm,sat. 10:00 am - 5:30 pm,sun. 12:00 pm - 5:00 pm
#     sun 10-9, mon-sat 9-10
#     """
#     print value , "===============string_to_dict"
#     days_hours = {}
#     # value = re.sub(':')
#     pattern = "(\[.*?\])"
#     hours = re.findall(pattern, value)
#     indexer = 0
#     if value.find("[") == 0:
#       return time_day_dict(value)


#     for hour in hours:
#         start = value.find("[") + indexer
#         end = value.find(']', start) +1
#         # print start, end, hour, indexer
#         # print value[indexer: end], '----'
#         days = re.findall(r'^(.*?)\[', value[indexer: end])[0]#.replace(',', '').replace('.', '').replace(':', '').strip()
#         days = days.replace(',', '').replace('.', '').replace(':', '')

#         days = days.strip().strip(' -')
#         print days
#         days_hours[days] = hour
#         indexer = end
#     return days_hours

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
    days_hours_copy = {k: v for k,v in days_hours.iteritems() if v}
    days = [x for x in days_hours.keys()]
    for day, hours in days_hours_copy.iteritems():
        print day
        if '-' in day:
            # print day
            """if dash separator given in keys"""
            del days_hours[day]

            start_day_index, end_day_index = [day_list.index(x.strip()) for x in day.split('-')]
            # print start_day_index, end_day_index
            if end_day_index <= start_day_index:
                expanded_days = day_list[start_day_index:] + day_list[:end_day_index+1]
                for expanded_day in expanded_days:
                    days_hours[expanded_day] = hours
            else:
                expanded_days = day_list[start_day_index:end_day_index+1]
                for expanded_day in expanded_days:
                    days_hours[expanded_day] = hours
        else:
            """check if multiple days given without separator"""
            multiple_days = re.findall(r'(\w{3})', day)
            if len(multiple_days) > 1:
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
        return 'Unhandled'


    # return days_hours

# day_expand(days_hours)

def sorted_output(value):
    output = []
    for i in day_list:
        output.append("{0}:{1}".format(i,value[i]))
    return '{ ' + ', '.join(output) + ' }'

class TestStringMethods(unittest.TestCase):

    def test_upper(self):
        value = replace_keywords(x.lower())
        self.assertTrue("a.m." not in value)
        self.assertTrue("p.m." not in value)
        self.assertTrue("am" not in value)



if __name__ == "__main__":
    #unittest.main()
# Monday - Wedneday 9:00am - 5:30pm, Thursday - 9:00am - 9:00pm, Friday - 9:00am - 5:30pm, Saturday - 9:00am - 4:00pm, Sunday 10:00am - 3:00pm
#monday - tuesday - wednesday closed,  thursday - 1600 - 2400, friday - 0500 - 0100, saturday - 0500 - 0100, sunday - 0500 - 0100

#mon-fri, sat: 9:00 am - 8:00 pm

#monday - 0700 - 1900, tuesday - 1900, wednesday - 0700 - 1900, thursday - 0700 - 1900, friday - 0700 - 1900, saturday - closed, sunday - closed
    x = """
09:30am-07:00pm(monday), 09:30am-07:00pm(tuesday), 09:30am-07:00pm(wednesday), 09:30am-07:00pm(thursday), 09:30am-07:00pm(friday), 09:00am-07:00pm(saturday), 12:00pm-05:00pm(sunday)
sunday : 06:00 - 21:00 monday : 06:00 - 21:00 tuesday : 06:00 - 21:00 wednesday : 06:00 - 21:00 thursday : 06:00 - 21:00 friday : 06:00 - 22:00 saturday : 06:00 - 22:00
monday 11:00-23:00 tuesday 11:00-23:00 wednesday 11:00-23:00 thursday 11:00-23:00 friday 11:00-00:00 saturday 11:00-00:00 sunday 11:00-22:30


10AM - 7PM (MON - WED, FRI & SAT)

sun 10-10, mon-sat 19-12

monday - friday: 9:00 am - 5:30 pm,saturday: 9:00 am - 1:00 pm,sunday: closed
monday - saturday: 8:00 am - 5:00 pm, sunday: closed

fri:9:00 am to 8:00 pm,mon:9:00 am to 7:00 pm,sat:9:00 am to 6:00 pm,thu:9:00 am to 7:00 pm,wed:9:00 am to 7:00 pm,sun:10:00 am to 4:00 pm,tue:9:00 am to 7:00 pm

friday:8:30am:6:00pm,wednesday:8:30am:6:00pm,sunday:0:00am:0:00am,tuesday:8:30am:6:00pm,thursday:8:30am:8:00pm,monday:8:30am:8:00pm,saturday:10:00am:4:00pm

Lundi :08h45 - 12h30/14h15 - 19h15,Mardi :08h45 - 12h30/14h15 - 19h15,Mercredi :08h45 - 12h30/14h15 - 19h15,Jeudi :08h45 - 12h30/14h15 - 19h15,Vendredi :08h45 -19h15,Samedi :08h45 -19h15,Dimanche :09h30 - 12h30

MON 0-2359,TUE 0-2359,WED 0-2359,THU 0-2359,FRI 0-2359,SAT 0-2359,SUN 0-2359

MON 0-845,MON 1800-2359,TUE 0-900,TUE 1800-2359,WED 0-900,WED 1800-2359,THU 0-900,THU 1800-2359,FRI 0-900,FRI 1800-2359,SAT 0-900,SAT 1300-2359,SUN 0-900,SUN 915-2359

Mon. & Thurs. 10:00 am - 8:00 pm,Tues., Wed., Fri. 10:00 am - 5:30 pm,Sat. 10:00 am - 5:30 pm,Sun. 12:00 pm - 5:00 pm

sun 10-9, mon-sat 9-10

sat: 9:00am - 12:00pm, tues: 9:00am - 5:00pm, thur: 9:00am - 5:00pm, mon: 9:00am - 5:00pm, fri: 9:00am - 5:00pm, wed: 9:00am - 5:00pm

hours of operation: mo-fr: 5:30 am - 4:30 pm|*receiving hours: mo-fr: 3:00 am - 5:00 am,mon-fri: 8:00 am - 2:00 pm (appointment required)


mon 8:30 am.-9:00 pm.,tue 8:30 am.-9:00 pm.,wed 8:30 am.-9:00 pm.,thu 8:30 am.-9:00 pm.,fri 8:30 am.-9:00 pm.,sat 8:30 am.-9:00 pm.,sun 11:00 am.-6:00 pm.

mon: 8h30 à 20h, tue: 8h30 à 20h, wed: 8h30 à 20h, thu: 8h30 à 20h, fri: 8h30 à 20h15, sat: 8h30 à 20h


mon: 9h à 19h30, tue: 9h à 19h30, wed: 9h à 19h30, thu: 9h à 19h30, fri: 9h à 20h, sat: 9h à 20h


mon: 8h45 à 19h30, tue: 8h45 à 19h30, wed: 8h45 à 19h30, thu: 8h45 à 19h30, fri: 8h45 à 20h, sat: 8h45 à 19h30

"""
    for i in filter(None,x.split('\n')):
        print i
        y = replace_keywords(i)
        print y, '---------------replace_keywords'
        y = replace_hours_without_time_delimeter(y)
        print y, '---------------replace_hours_without_time_delimeter'

        y = convert_to_24h(y)
        print y, '---------------convert_to_24h'

        y = replace_open_close_delimeter(y)
        print y, '---------------replace_open_close_delimeter'

        y = replace_hour_groups(y)
        print y, '---------------replace_hour_groups'

        try:
            y = string_to_dict(y)
        except Exception as e:
            # y = e
            print y, '---------------string_to_dict', e
        if isinstance(y, dict):
            y = day_expand(y)

            y = sorted_output(y)
            print y, '----------------day_expand'
        else:
            unhandled_patterns = y
            print unhandled_patterns
        break