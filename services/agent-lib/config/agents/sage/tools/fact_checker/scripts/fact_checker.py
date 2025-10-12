#!/usr/bin/env python3
"""Fact Checker Tool - Local to Sage Agent"""
import json
import sys
import re

KNOWN_FACTS = {
    "math": {
        "2+2=4": True,
        "pi>3": True,
        "sqrt(4)=2": True,
    },
    "science": {
        "earth_round": True,
        "water_boils_100c": True,
        "speed_of_light": "299,792,458 m/s",
    },
    "programming": {
        "python_interpreted": True,
        "c_compiled": True,
        "recursion_uses_stack": True,
    }
}

def normalize_claim(claim):
    """Normalize claim for comparison."""
    return re.sub(r'\s+', '', claim.lower())

def check_fact(claim, context=""):
    """Verify a factual claim."""
    claim_normalized = normalize_claim(claim)
    
    # Check mathematical expressions
    if any(op in claim for op in ['+', '-', '*', '/', '=', '<', '>']):
        try:
            # Simple eval for basic math (in production, use safer parser)
            if '=' in claim:
                left, right = claim.split('=')
                left_val = eval(left.strip())
                right_val = eval(right.strip())
                is_true = abs(left_val - right_val) < 0.0001
                confidence = 100 if is_true else 0
                return {
                    "verified": is_true,
                    "confidence": confidence,
                    "explanation": f"Mathematical verification: {left_val} {'==' if is_true else '!='} {right_val}"
                }
        except:
            pass
    
    # Check against known facts database
    for category, facts in KNOWN_FACTS.items():
        for fact_key, fact_value in facts.items():
            if fact_key in claim_normalized:
                return {
                    "verified": True,
                    "confidence": 95,
                    "category": category,
                    "explanation": f"Matches known fact in {category} category"
                }
    
    # Check for logical consistency keywords
    logical_keywords = ["always", "never", "all", "none", "must", "cannot"]
    has_absolute = any(keyword in claim.lower() for keyword in logical_keywords)
    
    if has_absolute:
        confidence = 30  # Absolute statements often need verification
        explanation = "Claim contains absolute statement - requires careful verification"
    else:
        confidence = 60  # Moderate confidence for general claims
        explanation = "No direct verification available - moderate confidence"
    
    return {
        "verified": None,  # Unknown
        "confidence": confidence,
        "explanation": explanation,
        "requires_research": True
    }

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "No parameters provided"}))
        sys.exit(1)
    
    try:
        params = json.loads(sys.argv[1])
        claim = params.get("claim", "")
        context = params.get("context", "")
        
        if not claim:
            raise ValueError("claim is required")
        
        result = check_fact(claim, context)
        result["claim"] = claim
        result["context"] = context
        
        print(json.dumps({"success": True, "result": result}))
        
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()
