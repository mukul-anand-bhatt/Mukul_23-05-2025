# File: db.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from models import Base
import pandas as pd

DATABASE_URL = "sqlite:///./stores.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.bind = engine

def init_db():
    Base.metadata.create_all(bind=engine)
    # load_data()

from datetime import datetime

def load_data():
    from models import StoreStatus, BusinessHours, StoreTimezones

    with SessionLocal() as session:
        session.query(StoreStatus).delete()
        session.query(BusinessHours).delete()
        session.query(StoreTimezones).delete()

        df_status = pd.read_csv("data/store_status.csv")
        df_hours = pd.read_csv("data/menu_hours.csv")
        df_tz = pd.read_csv("data/timezones.csv")

        # 👇 Convert timestamp string to datetime
        df_status['timestamp_utc'] = pd.to_datetime(df_status['timestamp_utc'].str.replace(' UTC', ''))

        for _, row in df_status.iterrows():
            session.add(StoreStatus(
                store_id=row.store_id,
                timestamp_utc=row.timestamp_utc,
                status=row.status
            ))

        for _, row in df_hours.iterrows():
            session.add(BusinessHours(
                store_id=row.store_id,
                dayOfWeek=row.dayOfWeek,
                start_time_local=row.start_time_local,
                end_time_local=row.end_time_local
            ))

        for _, row in df_tz.iterrows():
            session.add(StoreTimezones(
                store_id=row.store_id,
                timezone_str=row.timezone_str
            ))

        session.commit()
