# Service Monitor

A continuous monitoring application that pings IP addresses and ports to ensure services are alive.

## Features

- Monitors multiple IP:port combinations every second
- Saves timestamped results to a persistent file
- Resumes from previous state if interrupted
- Shows real-time status and statistics
- Configurable service list
- Graceful shutdown handling

## Usage

### Start Monitoring
```bash
python3 service_monitor.py
```

### View Statistics
```bash
python3 service_monitor.py stats
```

### View Configuration
```bash
python3 service_monitor.py config
```

## Configuration

Edit `monitor_config.json` to customize monitored services:

```json
{
  "services": [
    {"ip": "127.0.0.1", "port": 5000, "name": "Chat App"},
    {"ip": "127.0.0.1", "port": 2121, "name": "FTP Server"},
    {"ip": "8.8.8.8", "port": 53, "name": "Google DNS"}
  ],
  "check_interval": 1,
  "timeout": 5
}
```

## Files

- `service_monitor.py` - Main monitoring application
- `monitor_config.json` - Configuration file (auto-created)
- `monitor_results.json` - Results file with success counters per IP:port
- `README.md` - This documentation

## Output Format

Real-time monitoring displays:
```
[timestamp] [✓/✗] [service_name] ([ip]:[port]) - [response_time]ms - [message] [Total successful: count]
```

Results are saved in JSON format with success counters:
```json
{
  "last_updated": "2024-01-15T10:30:45.123",
  "success_counts": {
    "127.0.0.1:5000": 45,
    "8.8.8.8:53": 67
  },
  "service_details": {
    "127.0.0.1:5000": {
      "name": "Chat App",
      "ip": "127.0.0.1",
      "port": 5000,
      "successful_pings": 45
    }
  }
}
```

## Default Services

The application monitors these services by default:
- Chat App (localhost:5000)
- FTP Server (localhost:2121)
- Ollama API (localhost:11434)
- PostgreSQL (localhost:5432)
- Google DNS (8.8.8.8:53)
- Cloudflare DNS (1.1.1.1:53)

## Persistence

- Results are continuously saved to `monitor_results.jsonl`
- If the application is restarted, it resumes from the last checkpoint
- All historical data is preserved
- Statistics can be generated from historical data

## Example Output

```
============================================================
SERVICE MONITOR STARTED
============================================================
Monitoring 6 services
Check interval: 1 second
Results file: monitor_results.jsonl
Config file: monitor_config.json

Press Ctrl+C to stop monitoring

Status format: [timestamp] [status] [service] - [response_time] - [message]
============================================================
2024-01-15T10:30:45.123 ✓ Chat App (127.0.0.1:5000) - 12.5ms - Connected successfully
2024-01-15T10:30:45.456 ✗ FTP Server (127.0.0.1:2121) - 1000.0ms - Connection failed (error 61)
2024-01-15T10:30:45.789 ✓ Ollama API (127.0.0.1:11434) - 8.2ms - Connected successfully
```
