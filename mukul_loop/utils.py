import pytz
from datetime import datetime, timedelta, time
from collections import defaultdict

def get_local_time_range(start, end, timezone_str, hours=None, full_day=False):
    tz = pytz.timezone(timezone_str)
    local_periods = []
    current = start.astimezone(pytz.utc)
    end = end.astimezone(pytz.utc)
    while current <= end:
        local = current.astimezone(tz)
        day = local.weekday()
        if full_day:
            local_periods.append((current, end))
            break
        day_hours = [h for h in hours if h.dayOfWeek == day]
        for h in day_hours:
            start_time_obj = datetime.strptime(h.start_time_local, "%H:%M:%S").time()
            end_time_obj = datetime.strptime(h.end_time_local, "%H:%M:%S").time()

            start_local = datetime.combine(local.date(), start_time_obj)
            end_local = datetime.combine(local.date(), end_time_obj)

            start_utc = tz.localize(start_local).astimezone(pytz.utc)
            end_utc = tz.localize(end_local).astimezone(pytz.utc)

            if end_utc >= start and start_utc <= end:
                local_periods.append((max(start_utc, start), min(end_utc, end)))
        current += timedelta(days=1)
    return local_periods

def interpolate_status(status_data, periods):
    if not status_data:
        return timedelta(), sum((end - start for start, end in periods), timedelta())

    up = timedelta()
    down = timedelta()
    for period_start, period_end in periods:
        times = [s.timestamp_utc.replace(tzinfo=pytz.utc) for s in status_data if period_start <= s.timestamp_utc.replace(tzinfo=pytz.utc) <= period_end]
        states = [s.status for s in status_data if period_start <= s.timestamp_utc.replace(tzinfo=pytz.utc) <= period_end]

        if not times:
            down += (period_end - period_start)
            continue

        for i in range(len(times) - 1):
            duration = times[i + 1] - times[i]
            if states[i] == 'active':
                up += duration
            else:
                down += duration

        last_duration = period_end - times[-1]
        if states[-1] == 'active':
            up += last_duration
        else:
            down += last_duration

    return up, down
