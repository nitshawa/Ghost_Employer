# -*- coding: utf-8 -*-
import re
import datetime
from dateutil import parser

import unicodedata

import hoo_convertor2 as hc
import uniform_pattern as up
import normalizer as nz
import logging
import pygsheets
import csv
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

# need to import HOO module's Normalizer, uniform pattern, hoo_convertor2
# this is just for planet fitness brand, these type of formats are very less, hence 
# didn't inculded in HOO main module.

norm = nz.Normalizer()



uni_pat = up.UniformPattern()
hoo = hc.BusinessHours()
FORMAT = '[%(asctime)-15s  %(levelname)s ]: %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)

# test_string = 'Monday - Friday: 9:00 AM - 9:00 PM, Thursday - Friday: 10:00 aM - 5:00 PM , Saturday: 9:00 AM - 1:00 PM'
test_string = "24 Hours Monday through Friday  Monday at 12:00 AM until Friday at 10:00 PM Saturday and Sunday 7:00 AM - 7:00 PM"
day_list = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']

def update_until(match_group):
    print match_group.groupdict(), 'ddd'
    obj = match_group.groupdict()
    start_day = re.search(r'\w{3}',obj.get('start_day')).group(0)
    if start_day == 'sun':
        next_day_start = 'mon'
    else:
        next_day_start = day_list[day_list.index(start_day)+1]
    next_day_start_time = '12:00 am'
    end_day = re.search(r'\w{3}',obj.get('end_day')).group(0)
    end_day = day_list[day_list.index(end_day)-1]
    start_time = obj.get('start_time')
    end_time = '12:00 am'
    until_day = obj.get('end_day')
    until_day_start_time = end_time
    until_day_end_time = obj.get('end_time')

    return "{} : {}-{}, {}-{} : {}-{}, {} : {}-{}".format(start_day, start_time, end_time,
                                                            next_day_start, end_day, next_day_start_time, end_time,
                                              until_day, until_day_start_time, until_day_end_time)

def relevant_word_handle(text):
    """

    :param text: raw string before replacement
    :return: update the string with required words for conversions
    """
    print text
    formalize_string = norm.replace_keywords(text)
    logging.debug('replaced string- > {}'.format(formalize_string))
    # pattern = r'(?P<start_day>\w{3})\s*at\s*(?P<start_time>\d{1,2}:\d{2}\s*am|pm)\s*until\s*(?P<end_day>\w{3})\s*at\s*(?P<end_time>\d{1,2}:\d{2}\s*pm|am)'
    # pattern = r'(?P<start_day>\w{3})\s*at\s*(?P<start_time>\d{1,2}:\d{2}\s*(am|pm|amon))\s*(until|thru|-)\s*(?P<end_day>(\w{3}|friri))\s*at\s*(?P<end_time>\d{1,2}:\d{2}\s*(pm|am))'
    # pattern = r'(?P<start_day>\w{3})\s*at\s*(?P<start_time>\d{1,2}[:\d{2}\s*(am|pm|amon|a|p)]+)\s*(until|thru|-)\s*(?P<end_day>(\w{3}|friri))\s*at\s*(?P<end_time>\d{1,2}[:\d{2}\s*(pm|am|a|p)]+)'
    pattern = r'(?P<start_day>mon|tue|wed|thu|fri|sat|sun)\s*[at]*\s*(?P<start_time>\d{1,2}[:\d{2}\s*(am|pm|amon|a|p)]+)\s*(until|thru|-)\s*(?P<end_day>mon|tue|wed|thu|fri|sat|sun|friri)\s*[at]*\s*(?P<end_time>\d{1,2}[:\d{2}\s*(pm|am|a|p)]+)'
    # start_with_time_pattern = r'(?P<start_time>\s*\d{1,2}[:\d{2}\s*(am|pm|a|p)]+)\s*(?P<start_day>mon|tue|wed|thu|fri|sat|sun)\s*(until|thru|-)\s*(?P<end_time>\s*\d{1,2}[:\d{2}\s*(am|pm|a|p)]+)\s*(?P<end_day>mon|tue|wed|thu|fri|sat|sun|friri)'
    start_with_time_pattern = r'(?P<start_time>\s*\d{1,2}[:\d{2}\s*(am|pm|a|p)]+)\s*(?P<start_day>mon(?<!amon)|tue|wed|thu|fri|sat|sun)\s*(until|thru|-)\s*(?P<end_time>\s*\d{1,2}[:\d{2}\s*(am|pm|a|p)]+)\s*(?P<end_day>mon(?<!amon)|tue|wed|thu|fri|sat|sun|friri)'
    if re.search(pattern, formalize_string):

        formalize_string = re.sub(pattern, update_until, formalize_string)
    else:
        formalize_string = re.sub(start_with_time_pattern, update_until, formalize_string)

    print formalize_string
    formated_business_hours = hoo.convert_operating_hours(str(formalize_string))
    # print formalize_string.index('until')
    # day_names = re.findall(r'\w{3}', formalize_string.replace('until', ''))
    # indexer = 0
    # pos_of_day = []
    # for day_name in day_names:
    #     start = formalize_string.find(day_name, indexer)
    #     end = start + len(day_name)
    #     indexer = end
    #     pos_of_day.append([start, day_name])
    #     # print day_name_index
    # pos_of_day.sort(key=lambda x:x[0])
    # print pos_of_day
    # prev_day_until =
    logging.debug('formalize_string : {}'.format(formated_business_hours))

    return formated_business_hours
relevant_word_handle(" 9am - 5pm: Mon, Tues, Thur, Fri, 9.30am - 5pm: Wed, 9am - 12pm: Sat")

def download_gsheet(brand_name, sheet_link):
    sheet_key = re.findall(r'\/d\/(.*?)\/edit', sheet_link)[0]
    gc = pygsheets.authorize()

    sht1 = gc.open_by_key(sheet_key)
    wks1 = sht1.worksheet_by_title("hoo_test").get_all_values()
    wks1 = [[i.encode('utf-8') for i in x] for x in wks1]
    downloaded_csv = csv.writer(open('/Users/nitinsharma/Desktop/current_project/hours_of_operation/dump/' + brand_name + '.csv', 'wb'))
    downloaded_csv.writerows(wks1)

# output_csv = csv.writer(open('public_fitness9.csv', 'wb'))
# output_csv.writerow(['test_string', 'converted'])



def update_gsheet(brand_name, sheet_link):
    download_gsheet(brand_name, sheet_link)
    output_csv = csv.writer(
        open("/Users/nitinsharma/Desktop/current_project/hours_of_operation/shared_brands/done_" + brand_name + '.csv',
             'wb'))
    output_csv.writerow(["brand_name", "store_name", "type", "address_1",
                         "city", "state", "zipcode", "country_code", "phone_number",
                         "primary_sic", "secondary_sic", "latitude", "longitude",
                         "raw_business_hours", "converted_business_hours", "brand_id", "raw_address", "updated_date",
                         "url"])
    input_csv = csv.reader(open('/Users/nitinsharma/Desktop/current_project/hours_of_operation/dump/' + brand_name + '.csv', 'rb'))
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

        raw_business_hours = str(value[13]).replace('from', '').strip(' ,')
        try:
            formated_business_hours = relevant_word_handle(raw_business_hours)
            # output_csv.writerow([test_string, converted])
        except Exception as e:
            # output_csv.writerow([test_string, str(e)])/
            formated_business_hours = e
            pass
        output_csv.writerow([brand_name, store_name, store_type, address_1, city,
                             state, zipcode, country_code, phone_number, primary_sic,
                             secondary_sic, latitude, longitude, raw_business_hours,
                             formated_business_hours, brand_id, raw_address, updated_date, url])


brand_name = 'Planet Fitness'
sheet_link = 'https://docs.google.com/spreadsheets/d/1JYQBE35siqGaZb8cbZlvfSEgLdY7wmJkJ3uJ6u5QLfc/edit#gid=452361776'

# update_gsheet(brand_name, sheet_link)
# day_time_groups = uni_pat.replace_hour_groups(test_string)
# print 'day_time_groups--', day_time_groups
# before_day_expand = hoo.uniform_string_format(day_time_groups)
# print 'before_day_expand--', before_day_expand
# # after_day_expand = hoo.day_expand(day_time_groups)
# # print after_day_expand
#




#
# print start_day_index, end_day_index
# # import normalizer as nz
# #
# # a = nz.Normalizer()
# # print a.replace_keywords("")
#
#
# # def date_to_week_day(value):
# #     """
# #
# #     :param value: valid date format
# #     :return: Complete day name of the date (eg. Saturday)
# #     """
# #     formatted_date = parser.parse(value).strftime('%Y-%m-%d')
# #     return datetime.datetime.strptime(formatted_date, '%Y-%m-%d').strftime('%A')
# #
# #
# # def formatted_date(match_obj):
# #     return date_to_week_day(match_obj.group())
# #
# #
# # def check_string_for_date(value):
# #     """
# #     date format should be : YYYY[-/.]MM[-/.]DD
# #
# #     :param value: normalize test string
# #     :return: replace date into day of week
# #     """
# #     pattern = r'(?P<year>(?:19|20)\d\d)[- /.](?P<month>0[1-9]|1[012])[- /.](?P<date>0[1-9]|[12][0-9]|3[01])'
# #     value = re.sub(pattern, formatted_date, value)
# #     if re.search(r'[\d{4}][-/.]*\d{2}[-/.]\d{2}', value):
# #         assert False,  'invalid date format! required YYYY-MM-DD'
# #     return value
# #
# # print check_string_for_date("1900-12-22 : 19:00-10:00, 1900-11-22 : 19:00-10:00")
# #
# # class Person:
# #   def __init__(self, name):
# #
# #     self.name = name
# #   def cal_age(self, birth):
# #     today = datetime.date(2001,12,12)
# #     age = (today - birth).days / 365
# #     return age
# #
# #
# # # p1 = Person("John")
# # #
# # # print(p1.name)
# # # print(p1.cal_age(datetime.date(1971, 12, 31)))
# # #
# # #
#
#
# # def rational_working_hours(value):
# #     """
# #
# #     :param value: hoo test string after attempting uniform pattern
# #     :return: assertion passed test string else assert message
# #     """
# #     pattern = r'(?P<opening>\d{1,2}:\d{2}[:\d{2}]*)*[on]*-*(?P<closing>\d{1,2}:\d{2}[:\d{2}]*)*'
# #
# #     check_open_close_timing_groups = [x for x in re.findall(pattern, value) if x != ('', '')]
# #     no_of_time_groups = len(check_open_close_timing_groups)  # type: int
# #     no_of_valid_time_groups = []
# #
# #     for single_group in check_open_close_timing_groups:
# #         check_valid_single_group = len(filter(None, single_group))
# #
# #         if check_valid_single_group == 2:
# #             no_of_valid_time_groups.append(single_group)
# #     assert (no_of_time_groups == len(no_of_valid_time_groups)), "Irrational hours!!!"
# #     return value
# #
# # rational_working_hours('mon : 06:00-00:00, tue : 06:00-06:00')
