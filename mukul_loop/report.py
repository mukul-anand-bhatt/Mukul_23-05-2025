import pandas as pd
import os
import pytz
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from db import SessionLocal
from models import StoreStatus, BusinessHours, StoreTimezones
from utils import get_local_time_range, interpolate_status
import json

STATUS_FILE = 'output/status.json'

# Remove the local status tracking - main.py will handle this
# reports_status = {}

# def update_status(report_id, status):
#     """Update report status - this will be called from main.py"""
#     reports_status[report_id] = status

# def get_report_status(report_id):
#     """Get report status"""
#     return reports_status.get(report_id, "Not found")

def generate_report(report_id: str):
    try:
        db: Session = SessionLocal()
        stores = db.query(StoreStatus.store_id).distinct().all()
        stores = [s[0] for s in stores]

        max_timestamp = db.query(StoreStatus.timestamp_utc).order_by(StoreStatus.timestamp_utc.desc()).first()[0]
        now = max_timestamp.astimezone(pytz.utc)
        intervals = {
            'hour': now - timedelta(hours=1),
            'day': now - timedelta(days=1),
            'week': now - timedelta(days=7),
        }

        rows = []

        for store_id in stores:
            timezone = db.query(StoreTimezones).filter_by(store_id=store_id).first()
            timezone_str = timezone.timezone_str if timezone else 'America/Chicago'

            metrics = {
                'store_id': store_id
            }
            for label, start_time in intervals.items():
                start_time = start_time.astimezone(pytz.utc)

                status_data = db.query(StoreStatus).filter(
                    StoreStatus.store_id == store_id,
                    StoreStatus.timestamp_utc >= start_time,
                    StoreStatus.timestamp_utc <= now
                ).order_by(StoreStatus.timestamp_utc).all()

                biz_hours = db.query(BusinessHours).filter_by(store_id=store_id).all()

                if not biz_hours:
                    business_periods = get_local_time_range(start_time, now, timezone_str, full_day=True)
                else:
                    business_periods = get_local_time_range(start_time, now, timezone_str, hours=biz_hours)

                up, down = interpolate_status(status_data, business_periods)
                metrics[f'uptime_last_{label}'] = round(up.total_seconds() / 3600 if label != 'hour' else up.total_seconds() / 60, 2)
                metrics[f'downtime_last_{label}'] = round(down.total_seconds() / 3600 if label != 'hour' else down.total_seconds() / 60, 2)

            rows.append(metrics)

        df = pd.DataFrame(rows)
        os.makedirs('output', exist_ok=True)
        df.to_csv(f'output/{report_id}.csv', index=False)
        # Status will be updated by main.py, not here

    except Exception as e:
        print(f"[ERROR] Report generation failed for {report_id}: {e}")
        # Status will be updated by main.py, not here

def generate_single_store_report(report_id: str, store_id: str):
    """
    Generate detailed report for a single store/restaurant with day, week, and month data
    """
    try:
        db: Session = SessionLocal()
        
        # Check if store exists
        store_exists = db.query(StoreStatus).filter_by(store_id=store_id).first()
        if not store_exists:
            # Status will be updated by main.py, not here
            return

        # Get the latest timestamp to use as reference point
        max_timestamp = db.query(StoreStatus.timestamp_utc).order_by(StoreStatus.timestamp_utc.desc()).first()[0]
        now = max_timestamp.astimezone(pytz.utc)
        
        # Define time intervals - including month
        intervals = {
            'day': now - timedelta(days=1),
            'week': now - timedelta(days=7),
            'month': now - timedelta(days=30),  # Adding month data
        }

        # Get timezone for the store
        timezone = db.query(StoreTimezones).filter_by(store_id=store_id).first()
        timezone_str = timezone.timezone_str if timezone else 'America/Chicago'

        # Get business hours for the store
        biz_hours = db.query(BusinessHours).filter_by(store_id=store_id).all()

        metrics = {
            'store_id': store_id,
            'timezone': timezone_str,
            'report_generated_at': now.strftime('%Y-%m-%d %H:%M:%S UTC')
        }
        
        # Process each time interval
        for label, start_time in intervals.items():
            start_time = start_time.astimezone(pytz.utc)

            # Get all status data for this store in the time period
            status_data = db.query(StoreStatus).filter(
                StoreStatus.store_id == store_id,
                StoreStatus.timestamp_utc >= start_time,
                StoreStatus.timestamp_utc <= now
            ).order_by(StoreStatus.timestamp_utc).all()

            print(f"[INFO] Found {len(status_data)} status records for store {store_id} in last {label}")

            # Calculate business periods based on business hours
            if not biz_hours:
                # If no business hours defined, assume 24/7 operation
                business_periods = get_local_time_range(start_time, now, timezone_str, full_day=True)
                print(f"[INFO] No business hours found for store {store_id}, assuming 24/7 operation")
            else:
                business_periods = get_local_time_range(start_time, now, timezone_str, hours=biz_hours)
                print(f"[INFO] Using defined business hours for store {store_id}")

            # Calculate uptime and downtime
            up, down = interpolate_status(status_data, business_periods)
            
            # Convert to hours for all periods (more consistent reporting)
            uptime_hours = round(up.total_seconds() / 3600, 2)
            downtime_hours = round(down.total_seconds() / 3600, 2)
            total_business_hours = round((up + down).total_seconds() / 3600, 2)
            
            # Calculate uptime percentage
            uptime_percentage = round((uptime_hours / total_business_hours * 100), 2) if total_business_hours > 0 else 0
            
            # Store metrics
            metrics[f'uptime_last_{label}_hours'] = uptime_hours
            metrics[f'downtime_last_{label}_hours'] = downtime_hours
            metrics[f'total_business_hours_last_{label}'] = total_business_hours
            metrics[f'uptime_percentage_last_{label}'] = uptime_percentage
            
            # Additional info for debugging
            metrics[f'status_records_last_{label}'] = len(status_data)
            metrics[f'business_periods_last_{label}'] = len(business_periods)

        # Add business hours summary
        if biz_hours:
            business_schedule = {}
            for bh in biz_hours:
                day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                day_name = day_names[bh.dayOfWeek]
                business_schedule[day_name] = f"{bh.start_time_local} - {bh.end_time_local}"
            
            metrics['business_hours'] = str(business_schedule)
        else:
            metrics['business_hours'] = "24/7 (No specific hours defined)"

        # Create DataFrame with single row
        df = pd.DataFrame([metrics])
        os.makedirs('output', exist_ok=True)
        df.to_csv(f'output/{report_id}.csv', index=False)
        
        print(f"[SUCCESS] Single store report generated for {store_id}")
        print(f"[SUMMARY] Day: {metrics.get('uptime_last_day_hours', 0)}h up, Week: {metrics.get('uptime_last_week_hours', 0)}h up, Month: {metrics.get('uptime_last_month_hours', 0)}h up")
        
        # Status will be updated by main.py, not here

    except Exception as e:
        print(f"[ERROR] Single store report generation failed for {report_id}, store {store_id}: {e}")
        import traceback
        traceback.print_exc()
        # Status will be updated by main.py, not here
    finally:
        if 'db' in locals():
            db.close()


def get_store_summary(store_id: str):
    """
    Helper function to get a quick summary of store data availability
    """
    try:
        db: Session = SessionLocal()
        
        # Get basic store info
        total_records = db.query(StoreStatus).filter_by(store_id=store_id).count()
        
        if total_records == 0:
            return {"error": "Store not found"}
        
        # Get date range of available data
        oldest_record = db.query(StoreStatus.timestamp_utc).filter_by(store_id=store_id).order_by(StoreStatus.timestamp_utc.asc()).first()
        newest_record = db.query(StoreStatus.timestamp_utc).filter_by(store_id=store_id).order_by(StoreStatus.timestamp_utc.desc()).first()
        
        # Get timezone
        timezone = db.query(StoreTimezones).filter_by(store_id=store_id).first()
        timezone_str = timezone.timezone_str if timezone else 'America/Chicago'
        
        # Get business hours
        biz_hours = db.query(BusinessHours).filter_by(store_id=store_id).all()
        
        return {
            "store_id": store_id,
            "total_status_records": total_records,
            "data_available_from": oldest_record[0].strftime('%Y-%m-%d %H:%M:%S UTC') if oldest_record else None,
            "data_available_until": newest_record[0].strftime('%Y-%m-%d %H:%M:%S UTC') if newest_record else None,
            "timezone": timezone_str,
            "has_business_hours": len(biz_hours) > 0,
            "business_days_defined": len(biz_hours)
        }
        
    except Exception as e:
        return {"error": str(e)}
    finally:
        if 'db' in locals():
            db.close()
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