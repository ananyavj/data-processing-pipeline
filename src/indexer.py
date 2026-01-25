import os
import faiss
import numpy as np


import faiss
import numpy as np
import os


class LogIndexer:
    def __init__(self, embeddings, index_path="models/faiss.index"):
        """
        Build index once, then reuse saved version from disk.
        """

        self.index_path = index_path

        # convert embeddings to numpy
        self.embeddings = np.array(embeddings).astype("float32")

        dimension = self.embeddings.shape[1]

        # ---------- KEY LOGIC ----------
        if os.path.exists(index_path):
            print("Loading saved FAISS index from disk...")
            self.index = faiss.read_index(index_path)

        else:
            print("Building new FAISS index...")

            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(self.embeddings)

            faiss.write_index(self.index, index_path)
            print("Index saved to disk!")
        # --------------------------------


    def search(self, query_embedding, k=3):
        query_embedding = np.array([query_embedding]).astype("float32")
        distances, indices = self.index.search(query_embedding, k)
        return indices[0]


if __name__ == "__main__":
    from ingest import load_logs
    from cleaner import clean_logs
    from embedder import LogEmbedder

    logs = clean_logs(load_logs("data/raw_logs.json"))

    embedder = LogEmbedder()
    embeddings = embedder.embed_logs(logs)

    indexer = LogIndexer(embeddings)

    query_vec = embedder.model.encode("database error")

    results = indexer.search(query_vec, k=2)

    print("Top matches:")
    for i in results:
        print(logs[i])
