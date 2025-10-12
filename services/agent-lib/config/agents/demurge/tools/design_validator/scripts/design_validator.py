#!/usr/bin/env python3
"""Design Validator Tool - Local to Demurge Agent"""
import json
import sys

DESIGN_PATTERNS = {
    "api": {
        "best_practices": [
            "Use RESTful resource naming",
            "Version your API (e.g., /v1/)",
            "Use proper HTTP methods (GET, POST, PUT, DELETE)",
            "Return appropriate status codes",
            "Implement pagination for collections",
            "Use HTTPS for security"
        ],
        "anti_patterns": [
            "Verbs in URLs (use /users not /getUsers)",
            "Mixing singular and plural",
            "Not handling errors consistently"
        ]
    },
    "database": {
        "best_practices": [
            "Normalize data appropriately",
            "Use indexes on frequently queried columns",
            "Define foreign key constraints",
            "Use transactions for multi-step operations",
            "Plan for scalability"
        ],
        "anti_patterns": [
            "Over-normalization",
            "Missing indexes",
            "Storing computed values",
            "No backup strategy"
        ]
    },
    "architecture": {
        "best_practices": [
            "Separation of concerns",
            "Loose coupling, high cohesion",
            "Single Responsibility Principle",
            "Dependency injection",
            "Configuration over hardcoding"
        ],
        "anti_patterns": [
            "Tight coupling",
            "God objects",
            "Circular dependencies",
            "Hardcoded configuration"
        ]
    }
}

def validate_design(design_type, description):
    """Validate design against best practices."""
    if design_type not in DESIGN_PATTERNS:
        return {
            "valid": True,
            "score": 50,
            "message": f"No specific patterns for {design_type} yet",
            "suggestions": ["Review general design principles"]
        }
    
    patterns = DESIGN_PATTERNS[design_type]
    score = 75  # Base score
    suggestions = []
    
    # Simple heuristic checks
    desc_lower = description.lower()
    
    # Check for common anti-patterns
    for anti in patterns["anti_patterns"]:
        if any(word in desc_lower for word in anti.lower().split()):
            score -= 10
            suggestions.append(f"Avoid: {anti}")
    
    # Suggest best practices
    suggestions.extend([f"✓ {bp}" for bp in patterns["best_practices"][:3]])
    
    return {
        "valid": score >= 50,
        "score": max(0, min(100, score)),
        "design_type": design_type,
        "best_practices": patterns["best_practices"],
        "suggestions": suggestions
    }

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "No parameters provided"}))
        sys.exit(1)
    
    try:
        params = json.loads(sys.argv[1])
        design_type = params.get("design_type")
        description = params.get("description", "")
        
        if not design_type:
            raise ValueError("design_type is required")
        
        result = validate_design(design_type, description)
        print(json.dumps({"success": True, "result": result}))
        
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()
