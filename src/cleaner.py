def is_noise(log: dict) -> bool:
    """
    Returns True if this log is useless and should be removed.
    """

    level = log["level"]
    message = log["message"].lower()

    # drop all debug logs
    if level == "DEBUG":
        return True

    # drop boring system messages
    noise_words = ["heartbeat", "metrics", "healthcheck"]

    for word in noise_words:
        if word in message:
            return True

    return False


def clean_logs(logs: list) -> list:
    """
    Remove noisy logs and return only useful ones.
    """

    cleaned = []

    for log in logs:
        if not is_noise(log):
            cleaned.append(log)

    return cleaned


if __name__ == "__main__":
    from ingest import load_logs

    logs = load_logs("data/raw_logs.json")

    print("Before cleaning:", len(logs))

    cleaned = clean_logs(logs)

    print("After cleaning :", len(cleaned))
    print(cleaned[:3])
