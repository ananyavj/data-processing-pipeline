import json

def load_logs(path: str):
    """
    Reads a JSON log file and returns a list of log dictionaries.

    Example output:
    [
        {"timestamp": "...", "level": "INFO", "message": "..."},
        ...
    ]
    """

    with open(path, "r") as f:
        logs = json.load(f)

    return logs

if __name__ == "__main__":
    logs = load_logs("data/raw_logs.json")
    print(f"Loaded {len(logs)} logs")
    print(logs[:2])
