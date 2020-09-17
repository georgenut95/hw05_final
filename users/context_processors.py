import datetime as dt


def year(request):
    today = dt.datetime.today()
    return {'today': today}
