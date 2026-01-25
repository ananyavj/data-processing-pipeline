import requests
import json
import os

def ingest_file(filepath, source_name):
    """
    Ingest a JSON log file and tag it with a source name.
    This keeps logs from different files separate.
    """
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return
    
    with open(filepath) as f:
        logs = json.load(f)
    
    response = requests.post(
        f"http://localhost:8000/ingest?source={source_name}",
        json=logs
    )
    
    print(f"✅ Ingested {filepath} as source '{source_name}'")
    print(f"   Response: {response.json()}")
    return response.json()


def search_by_source(query, source_name=None):
    """
    Search logs, optionally filtered by source.
    """
    params = {"q": query, "k": 5}
    if source_name:
        params["source"] = source_name
    
    response = requests.get(
        "http://localhost:8000/search",
        params=params
    )
    
    results = response.json()
    
    if source_name:
        print(f"\n🔍 Search '{query}' in source '{source_name}': {len(results)} results")
    else:
        print(f"\n🔍 Search '{query}' across ALL sources: {len(results)} results")
    
    for i, log in enumerate(results, 1):
        print(f"  {i}. [{log['level']}] {log.get('source', 'N/A')}: {log['message'][:60]}...")
    
    return results


def get_summary_by_source(source_name=None):
    """
    Get log statistics, optionally filtered by source.
    """
    params = {}
    if source_name:
        params["source"] = source_name
    
    response = requests.get(
        "http://localhost:8000/summary",
        params=params
    )
    
    summary = response.json()
    
    if source_name:
        print(f"\n📊 Summary for source '{source_name}':")
    else:
        print(f"\n📊 Summary across ALL sources:")
    
    print(f"   Total logs: {summary['total']}")
    print(f"   By level: {summary['by_level']}")
    
    return summary


# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("MULTI-SOURCE LOG INGESTION DEMO")
    print("=" * 60)
    
    # Example 1: Ingest multiple files with different sources
    # ingest_file("data/webapp_logs.json", "webapp")
    # ingest_file("data/database_logs.json", "database")
    # ingest_file("data/api_logs.json", "api-service")
    
    # Example 2: Search only in specific source
    print("\n" + "=" * 60)
    print("DEMO: Source-Filtered Search")
    print("=" * 60)
    
    # Search only in payment-service logs (from our test)
    search_by_source("error", source_name="payment-service")
    
    # Search across all sources
    search_by_source("error")
    
    # Example 3: Get stats by source
    print("\n" + "=" * 60)
    print("DEMO: Source-Filtered Summary")
    print("=" * 60)
    
    get_summary_by_source("payment-service")
    get_summary_by_source()  # All sources
