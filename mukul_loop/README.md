# Store Monitoring System

A FastAPI-based backend system for monitoring restaurant uptime/downtime during business hours.

## Features

- **Database Integration**: SQLite database with SQLAlchemy ORM
- **Report Generation**: Asynchronous report generation with polling mechanism
- **Business Hours Support**: Handles store-specific business hours and timezones
- **Uptime/Downtime Calculation**: Interpolates status data to calculate accurate uptime/downtime
- **RESTful APIs**: Clean API endpoints for triggering and retrieving reports

## Setup Instructions

### Prerequisites
- Python 3.8+
- pip

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd mukul_loop
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python main.py
   ```

   The application will automatically:
   - Initialize the database
   - Load data from CSV files
   - Start the FastAPI server on `http://localhost:8000`

### Data Files Required

Place the following CSV files in the `data/` directory:
- `store_status.csv` - Store status data (store_id, timestamp_utc, status)
- `menu_hours.csv` - Business hours data (store_id, dayOfWeek, start_time_local, end_time_local)
- `timezones.csv` - Store timezone data (store_id, timezone_str)

## API Endpoints

### 1. Trigger Report Generation
```http
POST /trigger_report
```
**Response:**
```json
{
  "report_id": "uuid-string",
  "status": "Report generation started"
}
```

### 2. Get Report Status/Download
```http
GET /get_report/{report_id}
```
**Response:**
- If running: `{"status": "Running"}`
- If complete: CSV file download
- If failed: `{"status": "Failed: error message"}`

### 3. List All Reports
```http
GET /reports
```
**Response:**
```json
{
  "reports": {
    "report_id_1": "Complete",
    "report_id_2": "Running"
  }
}
```

### 4. Single Store Report
```http
POST /trigger_single_store_report/{store_id}
```
**Response:**
```json
{
  "report_id": "single_store_123_uuid",
  "store_id": "123",
  "status": "Single store report generation started"
}
```

### 5. Store Summary
```http
GET /store_summary/{store_id}
```
**Response:**
```json
{
  "store_id": "123",
  "total_status_records": 1000,
  "data_available_from": "2023-01-01 00:00:00 UTC",
  "data_available_until": "2023-12-31 23:59:59 UTC",
  "timezone": "America/Chicago",
  "has_business_hours": true,
  "business_days_defined": 7
}
```

## Report Schema

The generated CSV reports contain the following columns:
- `store_id`: Unique identifier for the store
- `uptime_last_hour`: Uptime in minutes for the last hour
- `uptime_last_day`: Uptime in hours for the last day
- `uptime_last_week`: Uptime in hours for the last week
- `downtime_last_hour`: Downtime in minutes for the last hour
- `downtime_last_day`: Downtime in hours for the last day
- `downtime_last_week`: Downtime in hours for the last week

## Architecture

### Database Schema
- **StoreStatus**: Stores hourly status polls (store_id, timestamp_utc, status)
- **BusinessHours**: Store business hours (store_id, dayOfWeek, start_time_local, end_time_local)
- **StoreTimezones**: Store timezone information (store_id, timezone_str)

### Key Components
1. **Data Loading**: Efficient CSV to database loading with proper data type handling
2. **Business Hours Calculation**: Converts local business hours to UTC for comparison
3. **Status Interpolation**: Interpolates status data to fill gaps between polls
4. **Asynchronous Processing**: Background report generation with status tracking

## Usage Example

```python
import requests

# 1. Trigger a report
response = requests.post("http://localhost:8000/trigger_report")
report_id = response.json()["report_id"]

# 2. Poll for completion
while True:
    status_response = requests.get(f"http://localhost:8000/get_report/{report_id}")
    if status_response.headers.get("content-type") == "text/csv":
        # Report is complete, save the CSV
        with open("report.csv", "wb") as f:
            f.write(status_response.content)
        break
    elif status_response.json()["status"] == "Running":
        time.sleep(5)  # Wait 5 seconds before polling again
    else:
        print(f"Report failed: {status_response.json()}")
        break
```

## Improvement Ideas

### 1. Performance Optimizations
- **Database Indexing**: Add composite indexes on (store_id, timestamp_utc) for faster queries
- **Batch Processing**: Process stores in batches to reduce memory usage
- **Caching**: Implement Redis caching for frequently accessed data
- **Connection Pooling**: Use database connection pooling for better performance

### 2. Scalability Enhancements
- **Microservices**: Split into separate services (data ingestion, report generation, API)
- **Message Queues**: Use RabbitMQ/Apache Kafka for report generation queuing
- **Horizontal Scaling**: Support multiple worker instances for report generation
- **Database Sharding**: Partition data by store_id for better performance

### 3. Data Management
- **Data Retention**: Implement automatic cleanup of old status data
- **Incremental Updates**: Support incremental data loading instead of full reload
- **Data Validation**: Add comprehensive data validation and error handling
- **Backup Strategy**: Implement automated database backups

### 4. Monitoring & Observability
- **Logging**: Structured logging with correlation IDs
- **Metrics**: Prometheus metrics for API performance and report generation times
- **Health Checks**: Comprehensive health check endpoints
- **Alerting**: Alerts for failed report generations or data issues

### 5. API Enhancements
- **Pagination**: Support pagination for large reports
- **Filtering**: Add filters for specific date ranges or store groups
- **Real-time Updates**: WebSocket support for real-time status updates
- **Rate Limiting**: Implement API rate limiting
- **Authentication**: Add JWT-based authentication

### 6. Business Logic Improvements
- **Custom Time Ranges**: Support custom time ranges for reports
- **Store Grouping**: Generate reports for store groups/chains
- **Trend Analysis**: Add historical trend analysis
- **Predictive Analytics**: Predict potential downtime based on patterns

### 7. User Experience
- **Web Interface**: Add a simple web UI for report management
- **Email Notifications**: Send email notifications when reports are complete
- **Report Templates**: Support different report formats (PDF, Excel)
- **Scheduled Reports**: Allow scheduling of regular reports

## Sample Output

A sample CSV output is available in the `output/` directory after running the application. The report includes:
- Store uptime/downtime calculations
- Business hours consideration
- Timezone-aware calculations
- Interpolated status data

## Demo Video

A demo video showing the complete flow is available at: [Demo Video Link]

The video demonstrates:
1. Starting the application
2. Triggering a report
3. Polling for completion
4. Downloading the generated CSV
5. Brief explanation of key components
