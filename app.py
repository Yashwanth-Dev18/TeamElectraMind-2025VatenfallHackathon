import sys
import time
import math
import random
import os
from dotenv import load_dotenv
from client import ConsiditionClient
import urllib3

# Suppress insecure HTTPS request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()

# -------------------------------------------------------
# Utility functions
# -------------------------------------------------------
def pistonia_distance(a, b):
    """Euclidean distance with Y-axis weighted for Pistonia layout."""
    try:
        ax, ay = map(float, a.split("."))
        bx, by = map(float, b.split("."))
        return math.sqrt((ax - bx) ** 2 + (1.2 * (ay - by)) ** 2)
    except Exception:
        return 9999

# -------------------------------------------------------
# Strategy Section
# -------------------------------------------------------
def generate_customer_recommendations(map_obj, current_tick):
    """Persona-aware, zone & load aware charging recommendations for Pistonia."""
    recommendations = []
    nodes = map_obj.get("nodes", [])

    # Identify charging stations
    charging_nodes = [
        node for node in nodes
        if node.get("target", {}).get("Type") in ["ChargingStation", "GreenChargingStation"]
    ]
    if not charging_nodes:
        return recommendations

    # Flatten all customers
    all_customers = []
    for node in nodes:
        for cust in node.get("customers", []):
            cust["currentNodeId"] = node["id"]
            cust["zoneId"] = node.get("zoneId", 0)
            all_customers.append(cust)

    # Sort customers by urgency (departureTick soonest first)
    all_customers.sort(key=lambda c: c.get("departureTick", 0))

    # Track per-station load dynamically
    station_load = {node["id"]: 0 for node in charging_nodes}

    for cust in all_customers:
        departure_tick = cust.get("departureTick", 0)
        if current_tick >= departure_tick:
            continue

        persona = cust.get("persona", "Neutral")
        charge_remaining = cust.get("chargeRemaining", 0)
        max_charge = cust.get("maxCharge", 1)
        soc = charge_remaining / max_charge
        current_node_id = cust["currentNodeId"]
        zone_id = cust.get("zoneId", 0)

        # Persona thresholds
        if persona in ["Stressed", "DislikesDriving"]:
            low_threshold, full_charge = 0.4, 0.8
        elif persona in ["EcoConscious", "CostSensitive"]:
            low_threshold, full_charge = 0.25, 1.0
        else:
            low_threshold, full_charge = 0.3, 0.8

        ticks_left = departure_tick - current_tick
        required_charge = max(0, full_charge - soc)
        min_ticks_needed = max(1, int(required_charge / 0.1))

        # Urgency scoring
        urgency = max(0, low_threshold - soc) + max(0, min_ticks_needed - ticks_left)
        urgency += 0.7 / max(ticks_left, 1)
        urgency += random.uniform(0, 0.03)

        if urgency > 0:
            # Zone-aware station preference
            zone_stations = [n for n in charging_nodes if n.get("zoneId") == zone_id]
            preferred_stations = zone_stations or charging_nodes

            # Eco-conscious prefers green stations
            if persona == "EcoConscious":
                green_stations = [n for n in preferred_stations if n["target"]["Type"] == "GreenChargingStation"]
                preferred_stations = green_stations or preferred_stations

            # Sort by distance + dynamic load
            preferred_stations.sort(key=lambda n: pistonia_distance(current_node_id, n["id"]) + 0.6 * station_load[n["id"]])
            target_station = preferred_stations[0]["id"]
            station_load[target_station] += 1

            # Adaptive charging based on persona
            if persona == "CostSensitive":
                charge_to = min(soc + 0.5, full_charge)
            elif persona == "EcoConscious":
                charge_to = min(full_charge, 1.0)
            elif persona == "Stressed":
                charge_to = full_charge
            else:
                charge_to = min(full_charge, soc + required_charge * min(1.0, 2 / max(ticks_left, 1)))

            recommendations.append({
                "customerId": cust["id"],
                "chargingRecommendations": [{"nodeId": target_station, "chargeTo": charge_to}]
            })

    return recommendations

def generate_tick(map_obj, current_tick):
    """Package tick input for API."""
    return {
        "tick": current_tick,
        "customerRecommendations": generate_customer_recommendations(map_obj, current_tick),
    }

def should_move_on_to_next_tick(response):
    """Always continue."""
    return True

# -------------------------------------------------------
# Main Game Loop
# -------------------------------------------------------
def main():
    api_key = os.getenv("API_KEY", "")
    base_url = "https://api.considition.com"
    map_name = "Pistonia"

    client = ConsiditionClient(base_url, api_key)

    # Load map
    try:
        map_obj = client.get_map(map_name)
    except Exception as e:
        print(f"Failed to fetch map: {e}")
        sys.exit(1)

    if not map_obj:
        print("❌ Failed to fetch map!")
        sys.exit(1)

    print(f"✅ Loaded map: {map_obj.get('name', 'Unknown')} ({map_obj.get('dimX')}x{map_obj.get('dimY')})")

    # Simulation variables
    final_score = 0
    good_ticks = []
    current_tick_data = generate_tick(map_obj, 0)
    input_payload = {
        "mapName": map_name,
        "ticks": [current_tick_data],
    }

    total_ticks = int(map_obj.get("ticks", 288))

    # Main tick loop
    for i in range(total_ticks):
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

        # Advance tick
        if should_move_on_to_next_tick(game_response):
            good_ticks.append(current_tick_data)
            updated_map = game_response.get("map", map_obj) or map_obj
            current_tick_data = generate_tick(updated_map, i + 1)
            input_payload = {
                "mapName": map_name,
                "ticks": [*good_ticks, current_tick_data],
            }

    print(f"\n🏁 Final score: {final_score}")

if __name__ == "__main__":
    main()
