import sys
import os

# Set UTF-8 encoding for stdout on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Add platform/src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from services.tomato_simulator.routes import search_food as tomato_search
from services.twiggy_simulator.routes import search_food as twiggy_search
from agent.graph.nodes.ranker import calculate_composite_score
from agent.graph.nodes.context_resolver import determine_meal_type_from_hour

def test_simulator_data():
    print("Testing Tomato Simulator search...")
    res_tomato = tomato_search(meal_type="dinner", limit=10)
    assert res_tomato.total > 0, "Tomato search returned 0 items"
    print(f"  [OK] Tomato returned {len(res_tomato.results)} items")

    print("Testing Twiggy Simulator search...")
    res_twiggy = twiggy_search(meal_type="dinner", limit=10)
    assert res_twiggy.total > 0, "Twiggy search returned 0 items"
    print(f"  [OK] Twiggy returned {len(res_twiggy.results)} items")

def test_meal_time_resolution():
    print("Testing Meal Time resolution...")
    assert determine_meal_type_from_hour(8) == "breakfast"
    assert determine_meal_type_from_hour(13) == "lunch"
    assert determine_meal_type_from_hour(17) == "snacks"
    assert determine_meal_type_from_hour(20) == "dinner"
    assert determine_meal_type_from_hour(1) == "late_night"
    print("  [OK] All meal times resolved accurately")

def test_ranking_algorithm():
    print("Testing Ranking & Prioritization algorithm...")
    res_tomato = tomato_search(meal_type="dinner", limit=5)
    res_twiggy = twiggy_search(meal_type="dinner", limit=5)
    combined = [m.model_dump() for m in res_tomato.results] + [m.model_dump() for m in res_twiggy.results]

    ranked = calculate_composite_score(combined)
    assert len(ranked) == 10
    assert "composite_score" in ranked[0]
    assert ranked[0]["composite_score"] >= ranked[-1]["composite_score"]
    top = ranked[0]
    print(f"  [OK] Top pick: {top['name']} on {top['platform']} (Price: Rs.{top['price']}, Rating: {top['rating']}, Delivery: {top['delivery_time_mins']}m, Score: {top['composite_score']})")

if __name__ == "__main__":
    print("=== Running KhaoAI Core Unit Tests ===")
    test_simulator_data()
    test_meal_time_resolution()
    test_ranking_algorithm()
    print("=== ALL CORE TESTS PASSED SUCCESSFULLY! ===")
