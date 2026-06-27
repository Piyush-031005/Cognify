import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import context_engine
import orchestrator

def mock_get_unified_state(email):
    if email == 'missing_memory@test.com':
        return {
            "metadata": {"schema_version": "1.0"},
            "memory": {},
            "telemetry": {}
        }
    return {
        "metadata": {"schema_version": "1.0"},
        "memory": {
            "forgetting": [{"node_id": "c1", "confidence": 0.9}],
            "active_misconceptions": [{"node_id": "m1", "confidence": 0.8}],
            "at_risk": [{"node_id": "c2", "confidence": 0.6}]
        },
        "telemetry": {}
    }

# Mock orchestrator call
orchestrator.get_unified_cognitive_state = mock_get_unified_state

def test_determinism():
    res1 = context_engine.generate_contextual_recommendations('student@test.com')
    res2 = context_engine.generate_contextual_recommendations('student@test.com')
    
    assert len(res1['recommendations']) == len(res2['recommendations']), "Non-deterministic length"
    for r1, r2 in zip(res1['recommendations'], res2['recommendations']):
        assert r1['priority'] == r2['priority'], "Non-deterministic priorities"
        assert r1['target'] == r2['target'], "Non-deterministic targets"

def test_missing_memory_graceful_degradation():
    res = context_engine.generate_contextual_recommendations('missing_memory@test.com')
    assert len(res['recommendations']) == 0, "Should handle missing memory gracefully"

def test_priority_sorting():
    res = context_engine.generate_contextual_recommendations('student@test.com')
    recs = res['recommendations']
    
    # Check if sorted
    priorities = [r['priority'] for r in recs]
    assert priorities == sorted(priorities, reverse=True), "Recommendations not sorted by priority!"

if __name__ == "__main__":
    print("\\nRunning Context Engine Tests...")
    test_determinism()
    test_missing_memory_graceful_degradation()
    test_priority_sorting()
    print("\\nALL CONTEXT ENGINE TESTS PASSED.")
