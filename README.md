
CSV - ![Link](https://drive.google.com/file/d/1cLDoBxx5juEii8OHeb8k410UAzTEo9L4/view?usp=sharing)


![WhatsApp Image 2025-05-23 at 13 43 22_1402b8d7](https://github.com/user-attachments/assets/25c242d2-ee37-4845-9887-87ff952b5f12)



Restaurant Monitoring System
A FastAPI-based system for monitoring restaurant uptime and generating detailed reports based on store status data, business hours, and timezone information.
Overview
This system tracks restaurant operational status and generates comprehensive reports showing uptime/downtime metrics across different time periods (hourly, daily, weekly, and monthly). It handles timezone conversions, business hours calculations, and provides both bulk and individual store reporting capabilities.
Features

Bulk Report Generation: Generate reports for all restaurants in the system
Individual Store Reporting: Get detailed reports for specific restaurants
Timezone Support: Handles different timezones for accurate local time calculations
Business Hours Integration: Respects individual restaurant operating hours
Asynchronous Processing: Background report generation with status tracking
CSV Export: All reports exported as downloadable CSV files

Database Schema
The system uses three main tables:
StoreStatus

store_id: Unique identifier for each restaurant
timestamp_utc: UTC timestamp of the status record
status: Current operational status ('active' or 'inactive')

BusinessHours

store_id: Restaurant identifier
dayOfWeek: Day of week (0=Monday, 6=Sunday)
start_time_local: Opening time in local timezone
end_time_local: Closing time in local timezone

StoreTimezones

store_id: Restaurant identifier
timezone_str: Timezone string (e.g., 'America/New_York')

API Endpoints
1. Generate All Stores Report
httpPOST /trigger_report
Response:
json{
  "report_id": "uuid-string"
}
Generates a comprehensive report for all restaurants in the system.
3. Get Report Status/Download
httpGET /get_report?report_id={report_id}
Responses:

If running: {"status": "Running"}
If complete: Downloads CSV file
If failed/not found: Error message

4. Store Data Summary
httpGET /store_summary?store_id={store_id}
Response:
json{
  "store_id": "store_123",
  "total_status_records": 1543,
  "data_available_from": "2024-01-01 00:00:00 UTC",
  "data_available_until": "2024-01-31 23:59:59 UTC",
  "timezone": "America/Chicago",
  "has_business_hours": true,
  "business_days_defined": 7
}
Sample CSV Output
The generated reports contain the following columns:
csvstore_id,uptime_last_hour,downtime_last_hour,uptime_last_day,downtime_last_day,uptime_last_week,downtime_last_week
store_001,55.5,4.5,22.3,1.7,150.2,17.8
store_002,60.0,0.0,24.0,0.0,168.0,0.0
store_003,45.2,14.8,18.5,5.5,125.7,42.3
Column Descriptions:

store_id: Restaurant identifier
uptime_last_hour: Minutes the store was operational in the last hour
downtime_last_hour: Minutes the store was down in the last hour
uptime_last_day: Hours the store was operational in the last 24 hours
downtime_last_day: Hours the store was down in the last 24 hours
uptime_last_week: Hours the store was operational in the last 7 days
downtime_last_week: Hours the store was down in the last 7 days

Installation & Setup
Prerequisites

Python 3.8+
PostgreSQL or SQLite database
Required Python packages (see requirements below)

Dependencies
bashpip install fastapi uvicorn sqlalchemy pandas pytz python-multipart
Database Setup

Create your database
Update database connection in db.py
Run the application to auto-create tables

Running the Application
bashuvicorn main:app --reload --host 0.0.0.0 --port 8000
The API will be available at http://localhost:8000
Project Structure
restaurant-monitoring/
├── main.py              # FastAPI application and routes
├── report.py            # Report generation logic
├── models.py            # SQLAlchemy database models
├── db.py                # Database configuration
├── utils.py             # Utility functions (included in report.py)
├── output/              # Generated reports directory
│   ├── status.json      # Report status tracking
│   └── *.csv            # Generated CSV reports
└── README.md            # This file
How It Works
Report Generation Process

Data Collection: System queries the database for store status records within specified time ranges
Timezone Conversion: Converts UTC timestamps to local store timezones
Business Hours Calculation: Determines operational periods based on defined business hours
Status Interpolation: Calculates uptime/downtime by analyzing status changes over time
Metrics Computation: Generates uptime/downtime statistics for different time periods
CSV Export: Formats data and saves as downloadable CSV files

Key Functions

generate_report(): Creates comprehensive reports for all stores
get_local_time_range(): Handles timezone conversions and business hour calculations
interpolate_status(): Calculates uptime/downtime from status data points
load_status()/save_status(): Manages report generation status tracking

Usage Examples
Generate Report for All Stores
bashcurl -X POST "http://localhost:8000/trigger_report"
# Response: {"report_id": "abc-123-def"}

# Check status
curl "http://localhost:8000/get_report?report_id=abc-123-def"
# Response: {"status": "Running"} or downloads CSV when complete
Check Store Data Availability
bashcurl "http://localhost:8000/store_summary?store_id=store_001"
Error Handling
The system includes comprehensive error handling:

Invalid store IDs return appropriate error messages
Database connection issues are logged and reported
Report generation failures are tracked in the status system
Missing business hours default to 24/7 operation

Performance Considerations

Reports are generated asynchronously to avoid blocking API requests
Database queries are optimized with proper indexing on store_id and timestamp_utc
Large datasets are processed in chunks to manage memory usage
Status tracking prevents duplicate report generation

Monitoring & Logs

Report generation progress is logged to console
Status information is persisted in output/status.json
Failed reports include error details in the status tracking

Limitations

Monthly data is calculated as last 30 days (not calendar month)
Assumes status remains constant between recorded data points
Business hours must be defined in local timezone format
Maximum report retention is not automatically managed
