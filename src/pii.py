import re


def mask_email(text):
    """
    Replace email addresses with [EMAIL]
    """
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.sub(pattern, '[EMAIL]', text)


def mask_ip(text):
    """
    Replace IP addresses with [IP]
    """
    # Match IPv4 addresses
    pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    return re.sub(pattern, '[IP]', text)


def mask_api_key(text):
    """
    Replace API keys/tokens with [TOKEN]
    Matches common patterns like 'key=xxx', 'token=xxx', 'Bearer xxx'
    """
    patterns = [
        r'(api[_-]?key|apikey)[=:\s]+[A-Za-z0-9_-]+',
        r'(token|bearer)[=:\s]+[A-Za-z0-9_-]+',
        r'(secret|password)[=:\s]+[A-Za-z0-9_-]+'
    ]
    
    result = text
    for pattern in patterns:
        result = re.sub(pattern, '[TOKEN]', result, flags=re.IGNORECASE)
    
    return result


def mask_pii(text):
    """
    Apply all PII masking functions to the text.
    This should be called before generating embeddings.
    """
    text = mask_email(text)
    text = mask_ip(text)
    text = mask_api_key(text)
    return text


def mask_logs(logs):
    """
    Apply PII masking to all log messages in a list.
    Returns a new list with masked logs.
    """
    masked_logs = []
    
    for log in logs:
        masked_log = log.copy()
        masked_log["message"] = mask_pii(log["message"])
        masked_logs.append(masked_log)
    
    return masked_logs


if __name__ == "__main__":
    # Test PII masking
    test_cases = [
        "User john@example.com logged in",
        "Connection from 192.168.1.1 established",
        "API request with token=abc123xyz failed",
        "Error: api_key=sk-1234567890 is invalid"
    ]
    
    print("Testing PII masking:")
    for text in test_cases:
        masked = mask_pii(text)
        print(f"Original: {text}")
        print(f"Masked:   {masked}\n")
