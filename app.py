import sys
import time
import math
import random
from client import ConsiditionClient
import os
from dotenv import load_dotenv

load_dotenv()
# -------------------------------------------------------
# Utility functions
# -------------------------------------------------------
def distance(a, b):
    """Simple Euclidean distance between two node IDs formatted like 'x.y'."""
    try:
        ax, ay = map(float, a.split("."))
        bx, by = map(float, b.split("."))
        return math.sqrt((ax - bx) ** 2 + (ay - by) ** 2)
    except Exception:
        return 9999  # fallback if format unexpected

# -------------------------------------------------------
# Strategy Section
# -------------------------------------------------------
def generate_customer_recommendations(map_obj, current_tick):
    """Main strategy to generate per-tick recommendations."""
    recommendations = []

    nodes = map_obj.get("nodes", [])
    charging_nodes = [
        node for node in nodes
        if node.get("target", {}).get("Type") in ["ChargingStation", "GreenChargingStation"]
    ]

    if not charging_nodes:
        return recommendations

    # Process customers sorted by departureTick (earliest first)
    all_customers = []
    for node in nodes:
        for cust in node.get("customers", []):
            cust["currentNodeId"] = node["id"]
            all_customers.append(cust)

    all_customers.sort(key=lambda c: c.get("departureTick", 0))

    for cust in all_customers:
        departure_tick = cust.get("departureTick", 0)
        if current_tick >= departure_tick:
            continue  # skip already departed customers

        persona = cust.get("persona", "Neutral")
        charge_remaining = cust.get("chargeRemaining", 0)
        max_charge = cust.get("maxCharge", 1)
        soc = charge_remaining / max_charge
        current_node_id = cust["currentNodeId"]

        # Persona-based thresholds
        low_threshold = 0.4 if persona in ["Stressed", "DislikesDriving"] else 0.25
        full_charge = 1.0 if persona in ["EcoConscious", "CostSensitive"] else 0.8

        # Estimate ticks needed to fully charge
        required_charge = full_charge - soc
        ticks_left = departure_tick - current_tick
        min_ticks_needed = max(1, int(required_charge / 0.1))

        # --- Always ensure enough charge to depart on time ---
        if soc < low_threshold or min_ticks_needed >= ticks_left:
            preferred_stations = [
                n for n in charging_nodes
                if n["target"]["Type"] == "GreenChargingStation"
            ]
            candidates = preferred_stations if preferred_stations else charging_nodes
            candidates.sort(key=lambda n: distance(current_node_id, n["id"]))
            target_station = candidates[0]["id"]

            recommendations.append({
                "customerId": cust["id"],
                "chargingRecommendations": [
                    {"nodeId": target_station, "chargeTo": full_charge}
                ]
            })

        # --- Occasional eco top-up for EcoConscious persona ---
        elif persona == "EcoConscious" and ticks_left > 5 and random.random() < 0.05:
            green_stations = [n for n in charging_nodes if n["target"]["Type"] == "GreenChargingStation"]
            if green_stations:
                target_station = random.choice(green_stations)["id"]
                recommendations.append({
                    "customerId": cust["id"],
                    "chargingRecommendations": [
                        {"nodeId": target_station, "chargeTo": 1.0}
                    ]
                })

    return recommendations

def generate_tick(map_obj, current_tick):
    """Package up a tick for the API."""
    return {
        "tick": current_tick,
        "customerRecommendations": generate_customer_recommendations(map_obj, current_tick),
    }

def should_move_on_to_next_tick(response):
    """Simple policy — always continue."""
    return True

# -------------------------------------------------------
# Main Game Loop
# -------------------------------------------------------
def main():
    api_key = os.getenv("API_KEY", "")
    base_url = "http://localhost:8080"
    map_name = "Turbohill"

    client = ConsiditionClient(base_url, api_key)

    # --- Load map ---
    try:
        map_obj = client.get_map(map_name)
    except Exception as e:
        print(f"Failed to fetch map: {e}")
        sys.exit(1)

    if not map_obj:
        print("❌ Failed to fetch map!")
        sys.exit(1)

    print(f"✅ Loaded map: {map_obj.get('name', 'Unknown')} ({map_obj.get('dimX')}x{map_obj.get('dimY')})")

    # --- Simulation variables ---
    final_score = 0
    good_ticks = []
    current_tick = generate_tick(map_obj, 0)
    input_payload = {
        "mapName": map_name,
        "ticks": [current_tick],
    }

    total_ticks = int(map_obj.get("ticks", 300))  # fallback to 300 ticks if unspecified

    # --- Main tick loop ---
    for i in range(total_ticks):
        while True:
            print(f"\nPlaying tick: {i}")
            start = time.perf_counter()
            try:
                game_response = client.post_game(input_payload)
            except Exception as e:
                print(f"Error posting game data: {e}")
                sys.exit(1)

            elapsed_ms = (time.perf_counter() - start) * 1000
            print(f"Tick {i} took: {elapsed_ms:.2f}ms")

            if not game_response:
                print("⚠️ No response from server.")
                sys.exit(1)

            # Extract and display scores
            final_score = game_response.get("score", 0)
            kwh_revenue = game_response.get("kwhRevenue", 0)
            completion_score = game_response.get("customerCompletionScore", 0)

            print(f"Partial score at tick {i}: {final_score} "
                  f"(kWhRevenue={kwh_revenue}, Completion={completion_score})")

            # --- Advance tick ---
            if should_move_on_to_next_tick(game_response):
                good_ticks.append(current_tick)
                updated_map = game_response.get("map", map_obj) or map_obj
                current_tick = generate_tick(updated_map, i + 1)
                input_payload = {
                    "mapName": map_name,
                    "ticks": [*good_ticks, current_tick],
                    "playToTick": i + 1
                }
                break

    print(f"\n🏁 Final score: {final_score}")

if __name__ == "__main__":
    main()
