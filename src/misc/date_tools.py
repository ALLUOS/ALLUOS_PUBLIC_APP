import datetime


def date_to_int(dt):
    return int(dt.strftime("%Y%m%d"))


def int_to_date(dt_int):
    return datetime.datetime.strptime(str(dt_int), "%Y%m%d").date()

