# !/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import re
import csv
import mysql.connector

# will use config file for mysql credentials
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

replacements = {
                            'mon': ['monday', 'montag', 'lundi', 'lunes', 'mon-mon', 'mo '],
                            'tue': ['tuesday', 'dienstag', 'mardi', 'martes', 'tues', 'tue-tue', 'tu '],
                            'wed': ['wednesday', 'mittwoch', 'mercredi', 'miércoles', 'wed-wed', 'we '],
                            'thu': ['thursday', 'donnerstag', 'jeudi', 'jueves', 'thurs', 'thur', 'thr', 'thu-thu', 'th '],
                            'fri': ['friday', 'freitag', 'vendredi', 'viernes', 'fir', 'fri-fri'  'fr '],
                            'sat': ['saturday', 'samstag', 'samedi', 'sábado', 'sat-sat', 'sa '],
                            'sun': ['sunday', 'sonntag', 'dimanche', 'domingo', 'sun-sun', 'su '],
                            'am': ['a.m', 'A.M.', 'AM', 'am.', '-am', 'a m', 'a.m.'],
                            'pm': ['p.m', 'P.M.', 'PM', 'pm.', '-pm', 'p m', 'p.m.'],
                            "closed": ["zamknięty", "cerrado", "fermé", "geschlossen"],
                            "open": ["otwarty", "abierto", "ouvert", "offen"],
                            "mon-fri": ['mo-fr'],
                            ' to ': [' à '],
                            'mon-sun': ['every day', 'everyday', 'all week', '7 days a week', 'seven days a week'],
                            '[]': ['closed - closed', 'closed-closed', 'close - close', 'close-close', 'closed', 'close'],
                            'mon-fri': ['weekday_hours', 'weekday'],
                            '': ['_hours'],
                            '&': ['\u0026'],
                            '[(00:00,23:59)]': ['24:00rs', '24:00urs', '24:00urs', '24:00s'],
                            '-': ['through', 'to', 'thuough', '\xe2\x80\x93', ' – '],
                            '-23:59': ['-midnight', ' - midnight']

                        }


def remove_html_tags(raw_string):
    tags = re.compile('<.*?>')
    clean_value = re.sub(tags, '', raw_string)
    return clean_value


def replace_keywords(value):
    value = remove_html_tags(value)
    value = value.lower()
    for (key, values) in replacements.iteritems():
        for rep in values:
            try:
                value = value.replace(rep, key)
            except:
                continue
    return value


def replace_french_from_to(value):
    x = re.sub(r'du (\w{3}) au (\w{3})', r'\1-\2', value)
    x = re.sub(r'le (\w{3})', r'\1', x)
    return x


def replace_hours_without_time_delimeter(value):
    return re.sub(r'(\d{1,2})(\d{2})', r'\1:\2', value)


def replace_hour_groups(value):
    p = r'\[(\(\d{2}:\d{2},\d{2}:\d{2}\))\]/\[(\(\d{2}:\d{2},\d{2}:\d{2}\))\]'
    return re.sub(p, r'[\1,\2]', value)


def without_am_pm(matchobj):
    obj = matchobj.groupdict()
    mins = obj.get('mins')

    start_hour = int(obj.get('start').strip())
    end_hour = int(obj.get('end').strip('-'))
    if start_hour != 0 and end_hour != 0:
        if end_hour <= start_hour:
            end_hour = (end_hour + 12) % 24
    return " {0:02d}{1:s}-{2:02d}".format(start_hour, mins, end_hour)


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

    if int_hour > 23:
        int_hour = 00

    if int_min > 59:
        int_min = 00
    return "{0:02d}:{1:02d}".format(int_hour, int_min)


def convert_to_24h(value):
    pattern = r"(?P<hour>\d{1,2})[:hH]{0,1}(?P<min>\d{0,2})[:.hH]{0,1}(?P<sec>\d{0,2})[' ']{0,1}(?P<ampm>\w{0,2})"
    raw_convertion = re.sub(pattern, replace_hours_for_match, value)
    valid_pattern = r"(?P<start>\s\d{2})(?P<mins>.*?)(?P<end>[-]\d{2})"
    valid_convert = re.sub(valid_pattern, without_am_pm, raw_convertion)
    return valid_convert


def replace_with_structured_hours(match_obj):
    return "['open': '{0}', 'close': '{1}']".format(match_obj.group(1), match_obj.group(2))


def replace_with_unstructured_hours(match_obj):
    return "[({0},{1})]".format(match_obj.group(1), match_obj.group(2))


def replace_open_close_delimeter(value):
    pattern = r'(\d{2}:\d{2})[\D]*(\d{2}:\d{2})'
    return re.sub(pattern, replace_with_unstructured_hours, value)


def time_day_dict(value):
    days_hours = {}
    pattern = "(\[.*?\])"
    hours = re.findall(pattern, value)
    indexer = 0

    for hour in hours:
        start = value.find("]", indexer) + 1
        end = value.find("[", start)
        if end == -1:  # to get last day name
            end = len(value)
        raw_days = value[start:end]

        # need to clean day names before this point
        days = ' '.join(raw_days.replace('(', '').replace(')', '').replace(',', '').replace('.', '').replace(':',
                                                                                                             '').split()).strip(
            '-').strip()
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
        start = value.find("[", indexer)
        end = value.find(']', start) + 1
        raw_days = re.findall(r'^(.*?)\[', value[indexer: end])[0]
        # need to clean day names before this point
        days = ' '.join(raw_days.replace(',', '').replace('.', '').replace(':', '').split()).strip('-').strip()
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
            eg.. tue :[(10:00,21:00)], wed :[(10:00,21:00)], thru  :[(10:00,21:00)]
    unhandled cases:
        if both separator and multiple days key appears : eg..
        mon-fri, sat: 9:00 am - 8:00 pm
        mon-tue-wed-fri 8.30am-6.30pm , thur 8.30am-5.30pm , sat 9am-12noon , sun closed

    """

    days_hours_copy = {k: v for k, v in days_hours.iteritems() if v}
    # days = [x for x in days_hours.keys()]
    for day, hours in days_hours_copy.iteritems():
        if '-' in day:

            """if dash separator given in keys"""
            del days_hours[day]

            start_day_index, end_day_index = [day_list.index(x.strip()) for x in day.split('-')]

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

    if sorted(days_hours.keys()) == sorted(day_list):
        return days_hours
    else:
        return 'Unhandled'  # keys contains garbage values like  call us, day name misspelled (mn, fi)


def sorted_output(value):
    """Temporay function to check output in sorted format"""
    output = []
    for i in day_list:
        output.append("{0}:{1}".format(i, value[i]))
    return '{ ' + ', '.join(output) + ' }'


if __name__ == "__main__":

    output_csv = csv.writer(open('store_hours.csv', 'wb'))
    output_csv.writerow(['input_string', 'output_dict', "unmatched"])

    """
    Excluding departmental hours/garbage
    As they can handled by scraping module in next re-run
    """
    query = """
    SELECT DISTINCT(raw_business_hours)
    FROM scrapers.locations
    WHERE lower(raw_business_hours) not REGEXP "hours|/|lobby|
    pharmacy|store|Drive|branch|today|24|shop|body|
    delivery|pick|partner|open-|sales"
    #LIMIT 30000;
    """

    cursor.execute(query)

    for value in cursor:
        if value is None:
            continue

        value = value[0]  # Access tuple from dataset

        if not isinstance(value, str) and not isinstance(value, unicode):
            continue

        value = value.replace("\n", " ").replace("\\n", " ").strip().lower()

        if value is "":
            continue

        try:

            keywords_from_raw_string = replace_keywords(value)
            replace_french_from_to_words = replace_french_from_to(keywords_from_raw_string)
            delimeter_added = replace_hours_without_time_delimeter(replace_french_from_to_words)
            converted_string_24_format = convert_to_24h(delimeter_added)
            add_open_close_delimeter = replace_open_close_delimeter(converted_string_24_format)
            made_hours_groups = replace_hour_groups(add_open_close_delimeter)
            not_matched = replace_hour_groups(made_hours_groups)
            day_hours_dict = string_to_dict(made_hours_groups)
            if isinstance(day_hours_dict, dict):
                try:
                    day_expanded_dict = day_expand(day_hours_dict)
                    sorted_output_str = sorted_output(day_expanded_dict)
                    output_csv.writerow([' '.join(value.split()), sorted_output_str, ' '.join(not_matched.split())])
                except:
                    y = 'Day expantion Failed : {0}'.format(day_expanded_dict)
            else:
                y = 'Unable to convert in dict : {0}'.format(day_hours_dict)
        except Exception as e:
            print e, value
            y = 'Unhandled formats : {0}'.format(value)
            pass

    cursor.close()
    cnx.close()