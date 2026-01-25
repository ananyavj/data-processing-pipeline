from sentence_transformers import SentenceTransformer


class LogEmbedder:
    def __init__(self):
        """
        Load the embedding model once when object is created.
        """

        self.model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )


    def embed_logs(self, logs: list):
        """
        Convert log messages into numeric vectors.
        """

        messages = []

        for log in logs:
            messages.append(log["message"])

        embeddings = self.model.encode(messages)

        return embeddings

if __name__ == "__main__":
    from ingest import load_logs
    from cleaner import clean_logs

    logs = load_logs("data/raw_logs.json")
    logs = clean_logs(logs)

    embedder = LogEmbedder()

    embeddings = embedder.embed_logs(logs)

    print("Number of logs:", len(logs))
    print("Embedding shape:", len(embeddings), len(embeddings[0]))
