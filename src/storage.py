import pickle
import os
import faiss


def save_logs(logs, path="models/logs.pkl"):
    """
    Save logs to disk using pickle.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(logs, f)
    print(f"Saved {len(logs)} logs to {path}")


def load_logs(path="models/logs.pkl"):
    """
    Load logs from disk using pickle.
    Returns empty list if file doesn't exist.
    """
    if not os.path.exists(path):
        print(f"No saved logs found at {path}")
        return []
    
    with open(path, "rb") as f:
        logs = pickle.load(f)
    print(f"Loaded {len(logs)} logs from {path}")
    return logs


def save_index(index, path="models/faiss.index"):
    """
    Save FAISS index to disk.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    faiss.write_index(index, path)
    print(f"Saved FAISS index to {path}")


def load_index(path="models/faiss.index"):
    """
    Load FAISS index from disk.
    Returns None if file doesn't exist.
    """
    if not os.path.exists(path):
        print(f"No saved index found at {path}")
        return None
    
    index = faiss.read_index(path)
    print(f"Loaded FAISS index from {path}")
    return index


if __name__ == "__main__":
    # Test storage functions
    test_logs = [
        {"timestamp": "2024-01-01", "level": "INFO", "message": "Test log 1"},
        {"timestamp": "2024-01-02", "level": "ERROR", "message": "Test log 2"}
    ]
    
    save_logs(test_logs)
    loaded = load_logs()
    assert len(loaded) == len(test_logs)
    print("✓ Storage test passed!")
