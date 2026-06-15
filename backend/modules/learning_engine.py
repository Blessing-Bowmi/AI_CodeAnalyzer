"""
Learning Refactor Engine (Innovative - Viva).
Learns from user-accepted refactors and improves suggestions over time.
"""

from collections import Counter
from database import get_connection

try:
    from sklearn.tree import DecisionTreeClassifier
    import numpy as np
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


def get_learning_stats() -> dict:
    """Get statistics about learned refactoring preferences."""
    conn = get_connection()
    data = conn.execute("SELECT * FROM learning_data ORDER BY created_at DESC").fetchall()
    conn.close()
    
    data_list = [dict(d) for d in data]
    
    if not data_list:
        return {
            "total_interactions": 0,
            "acceptance_rate": 0,
            "preferred_types": [],
            "avoided_types": [],
            "model_ready": False
        }
    
    total = len(data_list)
    accepted = len([d for d in data_list if d["was_accepted"]])
    rejected = total - accepted
    
    # Find preferred types
    accepted_types = Counter(d["refactor_type"] for d in data_list if d["was_accepted"])
    rejected_types = Counter(d["refactor_type"] for d in data_list if not d["was_accepted"])
    
    return {
        "total_interactions": total,
        "acceptance_rate": round(accepted / total * 100, 1) if total > 0 else 0,
        "accepted_count": accepted,
        "rejected_count": rejected,
        "preferred_types": accepted_types.most_common(5),
        "avoided_types": rejected_types.most_common(5),
        "model_ready": total >= 10
    }


def predict_acceptance(refactor_type: str) -> dict:
    """Predict if a user will accept a given refactor type based on history."""
    conn = get_connection()
    data = conn.execute("SELECT * FROM learning_data").fetchall()
    conn.close()
    
    data_list = [dict(d) for d in data]
    
    if len(data_list) < 5:
        return {
            "prediction": "unknown",
            "confidence": 0.5,
            "message": "Not enough data to make predictions. Need at least 5 interactions."
        }
    
    # Simple frequency-based prediction
    type_data = [d for d in data_list if d["refactor_type"] == refactor_type]
    
    if not type_data:
        # No data for this type, use overall acceptance rate
        overall_rate = len([d for d in data_list if d["was_accepted"]]) / len(data_list)
        return {
            "prediction": "likely_accept" if overall_rate > 0.5 else "likely_reject",
            "confidence": round(overall_rate, 2),
            "message": f"No history for '{refactor_type}'. Using overall acceptance rate: {overall_rate:.0%}"
        }
    
    accepted = len([d for d in type_data if d["was_accepted"]])
    rate = accepted / len(type_data)
    
    return {
        "prediction": "likely_accept" if rate > 0.5 else "likely_reject",
        "confidence": round(rate, 2),
        "message": f"Based on {len(type_data)} interactions, '{refactor_type}' has {rate:.0%} acceptance rate",
        "history_count": len(type_data)
    }


def reorder_suggestions(suggestions: list) -> list:
    """Reorder refactoring suggestions based on learned preferences."""
    stats = get_learning_stats()
    
    if not stats["model_ready"]:
        return suggestions
    
    preferred = dict(stats["preferred_types"])
    avoided = dict(stats["avoided_types"])
    
    def score(suggestion):
        rtype = suggestion.get("refactor_type", suggestion.get("type", ""))
        pref_score = preferred.get(rtype, 0)
        avoid_score = avoided.get(rtype, 0)
        return pref_score - avoid_score
    
    return sorted(suggestions, key=score, reverse=True)


def record_feedback(refactor_type: str, accepted: bool, context: str = "") -> dict:
    """Record user feedback for learning."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO learning_data (refactor_type, was_accepted, context) VALUES (?, ?, ?)",
        (refactor_type, 1 if accepted else 0, context)
    )
    conn.commit()
    conn.close()
    
    return {"recorded": True, "type": refactor_type, "accepted": accepted}
