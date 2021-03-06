import re
from datetime import datetime, date
from time import localtime, strftime


def extract_remainder_after_fragments(fragments, content):
    content = content.lower()
    for fragment in fragments:
        fragment = fragment.lower()
        try:
            idx = content.index(fragment)
            return content[idx + len(fragment) + 1:]
        except ValueError:
            continue  # or pass?
    return content


def epoch_time_to_digital(ftime):
    if ftime:
        struct_time = localtime(ftime)
        return strftime("%H:%M", struct_time)
    return None


def format_time_string(time_string):
    # format regexed matched string to be (24H) HH:MMa/pm
    if ':' in time_string:
        hours = time_string.split(":")[0]
        rest = time_string.split(":")[1]
        if len(hours) == 1:
            hours = "0" + hours
        if ('pm' in time_string) or ('am' in time_string):
            return hours + ":" + rest
        else:
            return hours + ":" + rest + "pm"
    elif len(time_string) == 1:
        time_string = "0" + time_string
        return time_string + ":00pm"
    elif len(time_string) == 2:
        return time_string + ":00pm"
    elif ('pm' in time_string) or ('am' in time_string):
        if len(time_string) == 3:
            return "0" + time_string[0] + ":00" + time_string[-2:]
        else:
            return time_string[:2] + ":00" + time_string[-2:]
    raise RuntimeError('Unhandled format_time_string case!')


def string_to_datetime(time_string):
    today_string = str(date.today())  # returns format %Y-%m-%d
    hour = int(time_string[:2])
    if 0 < hour <= 12:
        return datetime.strptime(today_string + " " + time_string, '%Y-%m-%d %I:%M%p')
    else:
        return datetime.strptime(today_string + " " + time_string, '%Y-%m-%d %H:%M%p')


def extract_time(content):
    time_specifiers = ["@", "at", "from"]
    time_specifiers_regex = "|".join(time_specifiers)
    r = re.compile(fr"(?:{time_specifiers_regex}) ((?:2[0-3]|[01]?[0-9])(?::[0-5]\d)*(?:[ap]m)*)")
    match = r.search(content.lower())
    if match is not None:
        for_time = match.group(1)
        for_time = format_time_string(for_time)
        date_time = string_to_datetime(for_time)
        if date_time > datetime.now():
            return date_time.timestamp()
        else:
            print("Tried to specify a time in the past! Ignoring time request...")
    return None
