from datetime import datetime
import pytz
from dateutil import tz


class DateFormat:
    @staticmethod
    def get(date):
        return datetime.strptime(date, '%Y-%m-%d').strftime('%d-%B-%Y')


class TimeFormat:
    @staticmethod
    def get(time):
        dt_str = time
        dt_format = "%Y-%m-%d %H:%M:%S"
        dt_utc = datetime.strptime(dt_str, dt_format)
        dt_utc = dt_utc.replace(tzinfo=pytz.UTC)
        local_zone = tz.tzlocal()
        dt_local = dt_utc.astimezone(local_zone)
        local_time_str = dt_local.strftime(dt_format)
        return local_time_str
