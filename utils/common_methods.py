from datetime import datetime

import pytz
from dateutil import tz


class Common:
    @staticmethod
    def change_date_format(date_format):
        return datetime.strptime(date_format, '%Y-%m-%d').strftime('%d-%b-%Y')

    @staticmethod
    def convert_utc_to_local_time(date_time_format):
        dt_format = "%Y-%m-%d %H:%M:%S"
        dt_utc = datetime.strptime(date_time_format, dt_format)
        dt_utc = dt_utc.replace(tzinfo=pytz.UTC)
        local_zone = tz.tzlocal()
        dt_local = dt_utc.astimezone(local_zone)
        local_date_time_str = dt_local.strftime(dt_format)
        return local_date_time_str

    @staticmethod
    def convert_local_time_to_utc(dt_format):
        formatting = "%Y-%m-%d %H:%M:%S"
        local_dt = datetime.strptime(dt_format, formatting)
        dt_utc = local_dt.astimezone(pytz.UTC)
        dt_utc_str = dt_utc.strftime(formatting)
        return dt_utc_str

    @staticmethod
    def convert_string_to_unicode_string(str_format):
        if "³" in str_format or "²" in str_format:
            last_string = str_format[-1]
            rest_string = str_format[:-1]
            unicode_string = ''.join(r'\u{:04X}'.format(ord(last_string)))
            result = rest_string + unicode_string
            return result
        else:
            return str_format
