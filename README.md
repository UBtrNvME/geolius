# IP Geolocation API

A RESTful API service for retrieving geolocation information based on IP addresses. Built with FastAPI, this service provides detailed location data including country, region, city, coordinates, timezone, and ISP information for any valid IPv4 or IPv6 address.

## Features

- **My IP Lookup**: Automatically detect and get geolocation data for the requester's IP address
- **Single IP Lookup**: Get geolocation data for a specific IP address
- **Comprehensive Error Handling**: Proper HTTP status codes and error messages
- **OpenAPI Specification**: Fully documented API with interactive documentation
- **Type Safety**: Full type hints and Pydantic validation
- **Async Support**: Built with async/await for high performance
- **Testing**: Comprehensive test suite with unit and integration tests

## Technology Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **Pydantic**: Data validation using Python type annotations
- **MaxMind GeoLite2**: Local IP geolocation database
- **geoip2**: Python library for MaxMind GeoIP2 databases
- **pytest**: Testing framework
- **ruff**: Fast Python linter and formatter
- **mypy**: Static type checker

## IP Geolocation Data Source

This service uses **MaxMind GeoLite2** local database for IP geolocation.

**Why MaxMind GeoLite2?**
- No rate limits - query as fast as needed
- No external API dependencies - works offline
- Fast local database queries
- Good data quality and accuracy
- Supports both IPv4 and IPv6
- Free for use (with attribution)
- Predictable performance

**Trade-offs:**
- Requires database setup and periodic updates
- Initial database download needed
- Storage space required (~50-100MB for City + ASN databases)
- Database needs to be updated monthly for accuracy

**Database Setup:**
1. Download GeoLite2 databases from MaxMind:
   - Sign up for a free MaxMind account at https://www.maxmind.com/en/geolite2/signup
   - Download `GeoLite2-City.mmdb` and `GeoLite2-ASN.mmdb`
   - Place them in the `data/` directory

2. The service will automatically use databases from:
   - `data/GeoLite2-City.mmdb` (required)
   - `data/GeoLite2-ASN.mmdb` (optional, for ISP/ASN data)

3. Configure paths in `.env` if needed:
```bash
MAXMIND_CITY_DB_PATH=data/GeoLite2-City.mmdb
MAXMIND_ASN_DB_PATH=data/GeoLite2-ASN.mmdb
```

See `DEVELOPMENT_NOTES.md` for detailed reasoning and production recommendations.

## Installation

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd geolius
```

2. Install dependencies using uv:
```bash
uv sync
```

Or using pip:
```bash
pip install -e ".[dev]"
```

3. Download MaxMind GeoLite2 databases:
   - Sign up for a free account at https://www.maxmind.com/en/geolite2/signup
   - Download `GeoLite2-City.mmdb` and `GeoLite2-ASN.mmdb`
   - Create a `data/` directory and place the databases there:
   ```bash
   mkdir -p data
   # Place GeoLite2-City.mmdb and GeoLite2-ASN.mmdb in data/
   ```

4. (Optional) Create a `.env` file for configuration:
```bash
# .env
MAXMIND_CITY_DB_PATH=data/GeoLite2-City.mmdb
MAXMIND_ASN_DB_PATH=data/GeoLite2-ASN.mmdb
HOST=0.0.0.0
PORT=8000
```

## Running the Service

### Development Server

Start the development server:
```bash
uvicorn geolius.main:app --reload --host 0.0.0.0 --port 8000
```

Or using uv:
```bash
uv run uvicorn geolius.main:app --reload
```

The API will be available at `http://localhost:8000`

### Production Server

For production, use a production ASGI server like Gunicorn with Uvicorn workers:
```bash
gunicorn geolius.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## API Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## API Endpoints

### Health Check

```http
GET /health
```

Returns the health status of the API service.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### My IP Geolocation

```http
GET /ip
```

Get geolocation data for the requester's IP address. The API automatically detects the client's IP address, including when behind proxies or load balancers.

**Example:**
```bash
curl http://localhost:8000/ip
```

**Response:**
```json
{
  "ip": "203.0.113.1",
  "country": "United States",
  "country_code": "US",
  "region": "California",
  "region_code": "CA",
  "city": "San Francisco",
  "postal_code": "94102",
  "latitude": 37.7749,
  "longitude": -122.4194,
  "timezone": "America/Los_Angeles",
  "isp": "Example ISP",
  "org": "Example Organization",
  "asn": "AS12345",
  "query_timestamp": "2024-01-15T10:30:00Z"
}
```

**Note:** The API automatically detects your IP address by checking:
- `X-Forwarded-For` header (for proxied requests)
- `X-Real-IP` header
- Direct client connection IP

### Single IP Geolocation

```http
GET /ip/{ip_address}
```

Get geolocation data for a specific IP address.

**Example:**
```bash
curl http://localhost:8000/ip/8.8.8.8
```

**Response:**
```json
{
  "ip": "8.8.8.8",
  "country": "United States",
  "country_code": "US",
  "region": "California",
  "region_code": "CA",
  "city": "Mountain View",
  "postal_code": "94043",
  "latitude": 37.4056,
  "longitude": -122.0775,
  "timezone": "America/Los_Angeles",
  "isp": "Google LLC",
  "org": "Google Public DNS",
  "asn": "AS15169",
  "query_timestamp": "2024-01-15T10:30:00Z"
}
```

## Error Handling

The API uses standard HTTP status codes:

- **200 OK**: Successful request
- **422 Unprocessable Entity**: Validation error (invalid IP address format)
- **404 Not Found**: IP address not found or no geolocation data available
- **500 Internal Server Error**: Internal server error
- **503 Service Unavailable**: Database unavailable or not found

Error responses follow this format:
```json
{
  "error": "Error type",
  "detail": "Detailed error message",
  "status_code": 400
}
```

## Testing

Run the test suite:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=geolius --cov-report=html
```

View coverage report:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Test Structure

- `tests/test_ip_validator.py`: IP address validation tests
- `tests/test_geolocation_service.py`: Service layer tests with mocking
- `tests/test_routes.py`: API endpoint integration tests
- `tests/test_models.py`: Pydantic model validation tests

## Code Quality

### Linting

Run ruff linter:
```bash
ruff check app tests
```

Auto-fix issues:
```bash
ruff check --fix app tests
```

Format code:
```bash
ruff format app tests
```

### Type Checking

Run mypy:
```bash
mypy app
```

## Project Structure

```
geolius/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── routes.py            # API routes
│   ├── models.py            # Pydantic models
│   ├── geolocation_service.py  # IP geolocation service
│   ├── ip_validator.py      # IP validation utilities
│   ├── exceptions.py        # Custom exceptions
│   └── config.py            # Configuration
├── tests/
│   ├── __init__.py
│   ├── test_ip_validator.py
│   ├── test_geolocation_service.py
│   ├── test_routes.py
│   └── test_models.py
├── openapi.yaml             # OpenAPI specification
├── pyproject.toml           # Project configuration
├── README.md                # This file
└── DEVELOPMENT_NOTES.md     # Development reflection
```

## API Design Decisions

1. **RESTful Design**: Follows REST principles with clear resource naming (`/ip/{ip_address}`)
2. **My IP Endpoint**: Simple `GET /ip` endpoint that automatically detects the requester's IP address
3. **Error Handling**: Consistent error response format across all endpoints
4. **Async Architecture**: Full async/await support for better performance with concurrent requests
5. **Type Safety**: Comprehensive type hints and Pydantic validation for reliability
6. **OpenAPI First**: OpenAPI spec serves as the source of truth for API documentation

## License

This project is provided as-is for demonstration purposes.

## Contributing

This is a demonstration project. For production use, please refer to `DEVELOPMENT_NOTES.md` for recommendations on production readiness improvements.
