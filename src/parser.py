"""
Raw Log File Parser

Converts raw log files (.log, .txt, .json) into structured JSON format
compatible with the existing ingestion pipeline.
"""

import re
import json
from typing import Optional
from datetime import datetime


def parse_line(line: str) -> Optional[dict]:
    """
    Parse a single log line into a structured dictionary.
    
    Supports common log formats:
    - ISO 8601: 2024-01-25T10:00:00Z INFO Application started
    - Syslog: Jan 25 10:00:00 INFO Application started
    - Custom: [2024-01-25 10:00:00] INFO: Application started
    
    Args:
        line: Raw log line string
    
    Returns:
        Dictionary with keys: timestamp, level, message
        Returns None if line cannot be parsed
    
    Example:
        >>> parse_line("2024-01-25T10:00:00Z INFO Application started")
        {'timestamp': '2024-01-25T10:00:00Z', 'level': 'INFO', 'message': 'Application started'}
    """
    line = line.strip()
    
    if not line:
        return None
    
    # Common log levels
    log_levels = r'(DEBUG|INFO|WARNING|WARN|ERROR|CRITICAL|FATAL)'
    
    # Pattern 1: ISO 8601 timestamp
    # Example: 2024-01-25T10:00:00Z INFO Application started
    pattern1 = rf'^(\d{{4}}-\d{{2}}-\d{{2}}T\d{{2}}:\d{{2}}:\d{{2}}(?:\.\d+)?Z?)\s+{log_levels}\s+(.+)$'
    match = re.match(pattern1, line, re.IGNORECASE)
    if match:
        return {
            "timestamp": match.group(1),
            "level": match.group(2).upper(),
            "message": match.group(3).strip()
        }
    
    # Pattern 2: Bracketed timestamp with colon separator
    # Example: [2024-01-25 10:00:00] INFO: Application started
    pattern2 = rf'^\[([^\]]+)\]\s+{log_levels}:?\s+(.+)$'
    match = re.match(pattern2, line, re.IGNORECASE)
    if match:
        return {
            "timestamp": match.group(1),
            "level": match.group(2).upper(),
            "message": match.group(3).strip()
        }
    
    # Pattern 3: Syslog-style (month day time)
    # Example: Jan 25 10:00:00 INFO Application started
    pattern3 = rf'^([A-Z][a-z]{{2}}\s+\d{{1,2}}\s+\d{{2}}:\d{{2}}:\d{{2}})\s+{log_levels}\s+(.+)$'
    match = re.match(pattern3, line, re.IGNORECASE)
    if match:
        return {
            "timestamp": match.group(1),
            "level": match.group(2).upper(),
            "message": match.group(3).strip()
        }
    
    # Pattern 4: Level first, then timestamp
    # Example: INFO 2024-01-25T10:00:00Z Application started
    pattern4 = rf'^{log_levels}\s+(\d{{4}}-\d{{2}}-\d{{2}}T\d{{2}}:\d{{2}}:\d{{2}}(?:\.\d+)?Z?)\s+(.+)$'
    match = re.match(pattern4, line, re.IGNORECASE)
    if match:
        return {
            "timestamp": match.group(2),
            "level": match.group(1).upper(),
            "message": match.group(3).strip()
        }
    
    # Pattern 5: Simple timestamp and message (assume INFO level)
    # Example: 2024-01-25T10:00:00Z Application started
    pattern5 = r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?)\s+(.+)$'
    match = re.match(pattern5, line)
    if match:
        return {
            "timestamp": match.group(1),
            "level": "INFO",
            "message": match.group(2).strip()
        }
    
    # If no pattern matches, return None (skip this line)
    return None


def detect_level_from_message(message: str) -> str:
    """
    Detect log level from message content.
    
    Rules:
    - Contains 'critical' → CRITICAL
    - Contains 'error' → ERROR
    - Contains 'warn' → WARNING
    - Otherwise → INFO
    """
    message_lower = message.lower()
    
    if 'critical' in message_lower:
        return 'CRITICAL'
    elif 'error' in message_lower:
        return 'ERROR'
    elif 'warn' in message_lower:
        return 'WARNING'
    else:
        return 'INFO'


def parse_raw_line(line: str, source_name: str) -> Optional[dict]:
    """
    Parse a raw line that doesn't match standard log formats.
    
    Converts any raw line into:
    {
        "timestamp": current_timestamp,
        "level": detected_level,
        "message": full_line,
        "source": filename
    }
    """
    line = line.strip()
    
    if not line:
        return None
    
    # Try structured parsing first
    parsed = parse_line(line)
    if parsed:
        parsed['source'] = source_name
        return parsed
    
    # Fallback: treat as raw line
    level = detect_level_from_message(line)
    timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    
    return {
        'timestamp': timestamp,
        'level': level,
        'message': line,
        'source': source_name
    }


def parse_file(filepath: str, source_name: str) -> list[dict]:
    """
    Parse a raw log file into a list of structured log dictionaries.
    
    Automatically detects file type:
    - .json: Parses as JSON array or JSON lines
    - .txt/.log: Parses each line as a log entry
    
    Args:
        filepath: Path to the raw log file
        source_name: Name to use for the 'source' field (typically the filename)
    
    Returns:
        List of log dictionaries, each with keys:
        - timestamp
        - level
        - message
        - source
    
    Example:
        >>> logs = parse_file("auth.log", "auth.log")
        >>> len(logs)
        150
        >>> logs[0]
        {'timestamp': '2024-01-25T10:00:00Z', 'level': 'INFO', 
         'message': 'User logged in', 'source': 'auth.log'}
    """
    logs = []
    lines_processed = 0
    
    try:
        # Detect if JSON file
        if filepath.endswith('.json'):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Try parsing as JSON array
                try:
                    data = json.loads(content)
                    
                    # Handle array of logs
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict):
                                # Ensure required fields exist
                                log = {
                                    'timestamp': item.get('timestamp', datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')),
                                    'level': item.get('level', 'INFO'),
                                    'message': item.get('message', str(item)),
                                    'source': source_name
                                }
                                logs.append(log)
                                lines_processed += 1
                    # Handle single log object
                    elif isinstance(data, dict):
                        log = {
                            'timestamp': data.get('timestamp', datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')),
                            'level': data.get('level', 'INFO'),
                            'message': data.get('message', str(data)),
                            'source': source_name
                        }
                        logs.append(log)
                        lines_processed += 1
                        
                except json.JSONDecodeError:
                    # Try parsing as JSON lines (one JSON object per line)
                    for line_num, line in enumerate(content.splitlines(), 1):
                        line = line.strip()
                        if not line:
                            continue
                        
                        try:
                            item = json.loads(line)
                            log = {
                                'timestamp': item.get('timestamp', datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')),
                                'level': item.get('level', 'INFO'),
                                'message': item.get('message', str(item)),
                                'source': source_name
                            }
                            logs.append(log)
                            lines_processed += 1
                        except json.JSONDecodeError:
                            # Skip invalid JSON lines
                            pass
            
            print(f"✓ Parsed {len(logs)} logs from JSON file {filepath}")
        
        else:
            # Handle .txt and .log files
            with open(filepath, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    lines_processed += 1
                    
                    # Use parse_raw_line which handles both structured and raw lines
                    parsed = parse_raw_line(line, source_name)
                    
                    if parsed:
                        logs.append(parsed)
            
            print(f"✓ Parsed {len(logs)} logs from {filepath}")
        
        return logs
    
    except FileNotFoundError:
        print(f"✗ File not found: {filepath}")
        return []
    except Exception as e:
        print(f"✗ Error parsing file {filepath}: {str(e)}")
        return []


if __name__ == "__main__":
    # Test the parser with some sample lines
    test_lines = [
        "2024-01-25T10:00:00Z INFO Application started successfully",
        "[2024-01-25 10:00:05] DEBUG: Loading configuration",
        "Jan 25 10:00:10 ERROR Database connection failed",
        "INFO 2024-01-25T10:00:15Z Processing request",
        "invalid log line without proper format",
        "2024-01-25T10:00:20Z User authentication completed",
    ]
    
    print("Testing parse_line():")
    print("-" * 60)
    for line in test_lines:
        result = parse_line(line)
        print(f"Input:  {line}")
        print(f"Output: {result}")
        print()
