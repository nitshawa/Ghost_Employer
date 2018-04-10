# coding : utf-8
import datetime
import re
days_hours = {}
# x = """mon :[(08:45,12:30),(14:15,19:15)],tue :[(08:45,12:30),(14:15,19:15)],wed :[(08:45,12:30),(14:15,19:15)],thu :[(08:45,12:30),(14:15,19:15)],fri :[(08:45,19:15)],sat :[(08:45,19:15)],sun :[(09:30,12:30)]
#     """

# x = "sun [(10:00,09:00),(10:00,08:00)], mon-sat [(10:00,10:00)]"
x = "sun 10-9, mon-sat 10-10"
# x = "mon -  tue -  wed - [], thu - [(16:00,24:00)], fri - [(05:00,01:00)], sat - [(05:00,01:00)], sun - [(05:00,01:00)]"
 # = re.compile(r'(?P<dayname>[A-Za-z]+\b)(?P<hours>\[(.*?)\])')

#mon -  tue - [], wed - []
def without_am_pm(matchobj):
    obj = matchobj.groupdict()
    mins = str(obj.get('mins'))
    start_hour = int(obj.get('start').strip())
    end_hour = int(obj.get('end').strip('-'))
    if end_hour <= start_hour:
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

    return "{0:02d}:{1:02d}".format(int_hour, int_min)



def convert_to_24h(value):
    pattern = r"(?P<hour>\d{1,2})[:hH]{0,1}(?P<min>\d{0,2})[:.hH]{0,1}(?P<sec>\d{0,2})[' ']{0,1}(?P<ampm>\w{0,2})"
    raw_convertion = re.sub(pattern, replace_hours_for_match, value)
    valid_pattern = r"(?P<start>\s\d{2})(?P<mins>.*?)(?P<end>[-]\d{2})"
    valid_convert = re.sub(valid_pattern, without_am_pm, raw_convertion)
    return valid_convert
# exit()
def string_to_dict(value):
    # value = without_am_pm()
    days_hours = {}
    pattern = "(\[.*?\])"
    hours = re.findall(pattern, value)

    indexer = 0
    for hour in hours:
        print hour

        start = value.find("[" ,indexer)
        end = value.find(']', start)+1
        raw_days = re.findall(r'^(.*?)$', value[indexer: start])[0]
    #     # need to clean day names before this point
        days = ' '.join(raw_days.replace(',', '').replace('.', '').replace(':','').split()).strip('-').strip()
        days_hours[days] = hour
        indexer = end
    return days_hours


"""assuming days after replacement function"""
day_list = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun' ]

# exit()
"""raw string converted to day_hours dict"""
# days_hours = {"fri - mon" : '[(01:00,08:45)]', 'thu' : '[(00:00,08:45)]', 'wed' : '[(00:00,08:45)]'}
# days_hours = {"sun" : "10:00-09:00", "mon & thu" :  "09:00-10:00", "tue., wed., fri" : "09:00-10:00"}
# days_hours = {'mon-wed' : '11am-10pm',   'thu-sat' : '11am-12am',   'sun' :' 11am-10pm'}
def day_expand(days_hours):
    days_hours_copy = {k: v for k,v in days_hours.iteritems() if v}
    days = [x for x in days_hours.keys()]
    for day, hours in days_hours_copy.iteritems():
        if '-' in day:

            """if dash separator given in keys"""
            del days_hours[day]

            start_day_index, end_day_index = [day_list.index(x.strip()) for x in day.split('-')]
            print start_day_index, end_day_index
            if end_day_index <= start_day_index:
                expanded_days = day_list[start_day_index:] + day_list[:end_day_index+1]
                for expanded_day in expanded_days:
                    days_hours[expanded_day] = hours
            else:
                expanded_days = day_list[start_day_index:end_day_index+1]
                for expanded_day in expanded_days:
                    days_hours[expanded_day] = hours
            print expanded_day
        else:
            """check if multiple days given without separator"""
            multiple_days = re.findall(r'(\w{3})', day)
            print multiple_days
            if len(multiple_days) > 0:
                del days_hours[day]
                for multiple_day in multiple_days:
                    days_hours[multiple_day] = hours

    '''updating dict with missing day as blank'''
    for day in day_list:
        if day not in days_hours.keys():
            days_hours[day] = []



    return days_hours

days_hours = string_to_dict(x)
day_expand(days_hours)
print days_hours