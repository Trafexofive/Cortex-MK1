#!/usr/bin/env python3
"""Knowledge Retriever Tool - Local to Sage Agent"""
import json
import sys

KNOWLEDGE_BASE = {
    "recursion": {
        "definition": "A function that calls itself to solve a problem by breaking it into smaller subproblems",
        "key_concepts": ["base case", "recursive case", "stack", "termination condition"],
        "examples": ["factorial", "fibonacci", "tree traversal"],
        "sources": ["SICP", "Algorithm Design Manual"]
    },
    "streaming": {
        "definition": "Processing data in real-time as it arrives, rather than waiting for complete dataset",
        "key_concepts": ["continuous processing", "low latency", "back-pressure", "event-driven"],
        "examples": ["video streaming", "data pipelines", "real-time analytics"],
        "sources": ["Stream Processing Fundamentals", "Reactive Systems"]
    },
    "agent": {
        "definition": "An autonomous entity that perceives its environment and takes actions to achieve goals",
        "key_concepts": ["autonomy", "reactivity", "proactivity", "social ability"],
        "examples": ["AI agents", "software agents", "intelligent assistants"],
        "sources": ["Artificial Intelligence: A Modern Approach", "Multi-Agent Systems"]
    }
}

def search_knowledge(query, depth="thorough"):
    """Search knowledge base for query."""
    query_lower = query.lower()
    results = []
    
    # Search for matching topics
    for topic, content in KNOWLEDGE_BASE.items():
        if topic in query_lower or query_lower in topic:
            results.append({
                "topic": topic,
                "relevance": "high",
                **content
            })
        elif any(concept in query_lower for concept in content.get("key_concepts", [])):
            results.append({
                "topic": topic,
                "relevance": "medium",
                **content
            })
    
    # If no direct matches, provide general guidance
    if not results:
        results.append({
            "topic": "general",
            "relevance": "low",
            "definition": f"No specific knowledge found for '{query}'. This topic may require external research.",
            "key_concepts": ["research", "investigation", "analysis"],
            "examples": [],
            "sources": []
        })
    
    # Limit results based on depth
    if depth == "quick":
        results = results[:1]
    elif depth == "thorough":
        results = results[:3]
    
    return {
        "query": query,
        "depth": depth,
        "results_count": len(results),
        "results": results
    }

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "No parameters provided"}))
        sys.exit(1)
    
    try:
        params = json.loads(sys.argv[1])
        query = params.get("query", "")
        depth = params.get("depth", "thorough")
        
        if not query:
            raise ValueError("query is required")
        
        result = search_knowledge(query, depth)
        print(json.dumps({"success": True, "result": result}))
        
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()
