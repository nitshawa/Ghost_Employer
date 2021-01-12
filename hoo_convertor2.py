# !/usr/bin/env python
# Author : Nitin Sharma
# -*- coding: utf-8 -*-

import re
import json


import uniform_pattern as up


class BusinessHours:
    """

    Standardisation for business hours variations.
    Maintain a uniform output from the input test string.

    output is json format:
    for instance:
    [{'start_time': '07:00:00', 'end_time': '23:00:00', 'days': ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']}]

    """

    def __init__(self):
        self.formation = up.UniformPattern()
        self.day_list = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
        self.days_hours = {}

    def time_day_format(self, value):
        """
        :param: string of time day format eg:
            9am-10pm mon, 9am-10pm tue-fri

        :return: dict with day name as key and hours as value.
        """

        days_hours = {}
        pattern = r'(\[.*?\])'
        hours = re.findall(pattern, value)
        indexer = 0
        for hour in hours:
            start = value.find(']', indexer) + 1
            end = value.find('[', start)
            if end == -1:  # to get last day name
                end = len(value)
            # need to clean day names before this point
            raw_days = value[start:end]
            days = raw_days.strip(' (),.:').split(',')
            for day in days:
                day = day.strip(' (),.:')
                days_hours[day] = hour
            indexer = start
        return days_hours

    def uniform_string_format(self, text):
        """

        :param text: string containing day name and hours.
        :return: dict with day name as key and hours as value.
        """
        # value = text #testing hours max rule
        value = self.formation.replace_hour_groups(text)
        # print value, "replace hours groups"
        days_hours = {}
        pattern = r'(\[.*?\])'
        hours = re.findall(pattern, value)
        indexer = 0
        if value.find('[') == 0:
            return self.time_day_format(value)
        for hour in hours:
            start = value.find('[', indexer)
            end = value.find(']', start) + 1

            raw_days = re.findall(r'^(.*?)\[', value[indexer: end])[0]
            # need to clean day names before this point
            days = raw_days.strip(' (),.:').split(',')
            for day in days:
                day = day.strip(' (),.:')
                days_hours[day] = hour
            indexer = end
        return days_hours

    # def day_expand(self, text):
    #     """
    #
    #     :param text: dict with day name as key and hours as value.
    #     :return: value expand for days where dash separator is in key (day name)
    #     """
    #     days_hours = self.uniform_string_format(text)
    #     days_hours_copy = {k: v for k, v in days_hours.iteritems() if v}
    #     day_list = self.day_list
    #     for day, hours in days_hours_copy.iteritems():
    #         if '-' in day.strip(' ()/,;-.'):
    #
    #             """if dash separator given in keys"""
    #             del days_hours[day]
    #             start_day_index, end_day_index = [day_list.index(x.strip(' ()/,;-.')) for x in day.split('-')]
    #             if end_day_index <= start_day_index:
    #                 expanded_days = day_list[start_day_index:] + day_list[:end_day_index + 1]
    #                 for expanded_day in expanded_days:
    #                     days_hours[expanded_day] = hours
    #             else:
    #                 expanded_days = day_list[start_day_index:end_day_index + 1]
    #                 for expanded_day in expanded_days:
    #                     days_hours[expanded_day] = hours
    #         else:
    #             """check if multiple days given without separator"""
    #             multiple_days = re.findall(r'(\w{3})', day)
    #             if len(multiple_days) > 0:
    #                 del days_hours[day]
    #                 for multiple_day in multiple_days:
    #                     days_hours[multiple_day] = hours
    #
    #     """updating dict with missing day as blank"""
    #     for day in day_list:
    #
    #         if day not in days_hours.keys():
    #             days_hours[day] = []
    #
    #     if sorted(days_hours.keys()) == sorted(day_list):
    #         return days_hours
    #
    #     else:
    #         return 'Invalid day name -> {}'.format(days_hours)

    def expand_short_range(self, long_day_range_key, days_hours):
        """

        :param long_day_range_key: long day range in days_hours dict
        :param days_hours: dict of day and time as key and value.
        :return: expanded days_hours according to short day range
        """
        day_list = self.day_list
        print long_day_range_key, "long_day_range_key", days_hours
        value_long_day_range_key = days_hours[long_day_range_key]

        del days_hours[long_day_range_key]
        days_hours_copy = {k: v for k, v in days_hours.iteritems() if v}
        # print long_day_range_key, "long_day_range_key"

        for day, hours in days_hours_copy.iteritems():
            if '-' in day.strip(' ()/,;-.'):
                """if dash separator given in keys"""
                del days_hours[day]
                start_day_index, end_day_index = [day_list.index(x.strip(' ()/,;-.')) for x in day.split('-')]
                if end_day_index <= start_day_index:  # sun-mon
                    expanded_days = day_list[start_day_index:] + day_list[:end_day_index + 1]
                    expanded_days = [x for x in expanded_days if x not in days_hours.keys()]
                    for expanded_day in expanded_days:
                        days_hours[expanded_day] = hours
                else:  # mon-sun
                    expanded_days = day_list[start_day_index:end_day_index + 1]
                    expanded_days = [x for x in expanded_days if x not in days_hours.keys()]
                    for expanded_day in expanded_days:
                        days_hours[expanded_day] = hours
        days_hours[long_day_range_key] = value_long_day_range_key

        print days_hours, "in expand_short_range"
        return days_hours
    # added day range function, as in few brands eddie, asked to prefer short day range over long day range
    def check_day_range(self, days_hours):
        """

        :param days_hours: json with day range as key and time as value
        :return: json with short range expansion
        """
        day_list = self.day_list
        days_range_keys = days_hours.keys()
        long_day_gap = 0
        long_day_range = ""
        for day in days_range_keys:
            if '-' in day:
                # print day
                start_day_index, end_day_index = [day_list.index(x.strip(' ()/,;-.')) for x in day.split('-')]
                # print end_day_index, start_day_index
                if end_day_index <= start_day_index:  # sun-mon
                    expanded_days = day_list[start_day_index:] + day_list[:end_day_index + 1]
                    # print expanded_days
                    long_day_gap = len(expanded_days)
                    long_day_range = day
                    # print "in if -- ", long_day_gap
                else:  # mon-sun
                    expanded_days = day_list[start_day_index:end_day_index + 1]
                    # print expanded_days, "in else"
                    if len(expanded_days) >= long_day_gap:
                        long_day_gap = len(expanded_days)
                        # print "in else -- ", long_day_gap
                        long_day_range = day
        if long_day_gap != 0:
            # print long_day_gap, "short_day_gap", long_day_range
            days_hours = self.expand_short_range(long_day_range, days_hours)
            # print days_hours, "return of check_day_range"

            return days_hours
        else:
            return days_hours

    def day_expand(self, text):
        """

        :param text: dict with day name as key and hours as value.
        :return: value expand for days where dash separator is in key (day name)
        """
        days_hours = self.uniform_string_format(text)
        print days_hours
        days_hours = self.check_day_range(days_hours)
        days_hours_copy = {k: v for k, v in days_hours.iteritems() if v}
        day_list = self.day_list
        for day, hours in days_hours_copy.iteritems():
            # print day, hours, "-"*20
            if '-' in day.strip(' ()/,;-.'):
                """if dash separator given in keys"""
                del days_hours[day]
                start_day_index, end_day_index = [day_list.index(x.strip(' ()/,;-.')) for x in day.split('-')]
                if end_day_index <= start_day_index:  # sun-mon
                    expanded_days = day_list[start_day_index:] + day_list[:end_day_index + 1]
                    # print expanded_days, "expand"
                    expanded_days = [x for x in expanded_days if x not in days_hours.keys()]
                    # print expanded_days
                    for expanded_day in expanded_days:
                        days_hours[expanded_day] = hours
                else:  # mon-sun
                    expanded_days = day_list[start_day_index:end_day_index + 1]
                    expanded_days = [x for x in expanded_days if x not in days_hours.keys()]
                    # print expanded_days, "                print expanded_days"

                    for expanded_day in expanded_days:
                        days_hours[expanded_day] = hours

            else:
                """check if multiple days given without separator"""
                multiple_days = re.findall(r'(\w{3})', day)
                print "multiple days---", multiple_days
                if len(multiple_days) > 0:
                    del days_hours[day]
                    for multiple_day in multiple_days:
                        days_hours[multiple_day] = hours
            # print days_hours, "after max", "*"*18
        """updating dict with missing day as blank"""
        for day in day_list:

            if day not in days_hours.keys():
                days_hours[day] = []

        if sorted(days_hours.keys()) == sorted(day_list):
            return days_hours

        else:
            return 'Invalid day name -> {}'.format(days_hours)

    def output_format_json(self, value):
        """

        :param value: dict with day name as key and hours as value.
        :return: update dict into required format shared by Eddie:
        for instance:
        [{'start_time': '07:00:00', 'end_time': '23:00:00', 'days': ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']}]

        """
        day_list = self.day_list
        value = self.day_expand(value)
        final_output = []
        unique = set([x for x in value.values() if type(x) is not list])
        formatted_output = {}
        for unique_val in unique:
            shared_keys = []
            for key, val in value.iteritems():
                if value[key] == unique_val:
                    shared_keys.append(key)
            formatted_output[unique_val] = shared_keys

        for key, val in formatted_output.iteritems():

            time_blocks = re.findall(r'\(.*?\)', key)
            for time_block in time_blocks:
                combined_days = {}
                start_time = re.search(r'\((\d{2}:\d{2}[:\d{2}]*)\,', time_block).group(1)
                end_time = re.search(r',(\d{2}:\d{2}[:\d{2}]*)\)', time_block).group(1)
                start_time = start_time.strip(' :')
                end_time = end_time.strip(' :')
                if len(start_time) == 5:
                    combined_days['start_time'] = '{}:00'.format(start_time)
                else:
                    combined_days['start_time'] = '{}'.format(start_time)
                if len(end_time) == 5:
                    combined_days['end_time'] = '{}:00'.format(end_time)
                else:
                    combined_days['end_time'] = '{}'.format(end_time)

                combined_days['days'] = val

                combined_days['days'].sort(key=lambda x: day_list.index(x))
                final_output.append(combined_days)

        if len(final_output) == 0:
            return []
        return json.dumps(final_output)

    def convert_operating_hours(self, text):
        """

        :param text: string that need to be conversion
        :return: converted raw_business_hours into valid output format
        for instance:
        [{'start_time': '07:00:00', 'end_time': '23:00:00', 'days': ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']}]

        """
        assert isinstance(text, str), 'Invalid type of value {}'.format(type(text))
        return self.output_format_json(text)
