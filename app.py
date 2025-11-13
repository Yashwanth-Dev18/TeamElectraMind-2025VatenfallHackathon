import sys
import time
from client import ConsiditionClient


# --- Strategy Section ---
def generate_customer_recommendations(map_obj, current_tick):
    recommendations = []

    # Step 1: Find all valid charging stations
    charging_nodes = [
        node["id"] for node in map_obj.get("nodes", [])
        if node.get("target", {}).get("Type") in ["ChargingStation", "GreenChargingStation"]
    ]

    for node in map_obj.get("nodes", []):
        customers = node.get("customers", [])
        for cust in customers:
            # Skip customers who haven't started yet
            if current_tick < cust.get("departureTick", 0):
                continue

            charge_remaining = cust.get("chargeRemaining", 0)
            max_charge = cust.get("maxCharge", 1)

            # If battery < 30% and we have any charging stations
            if charge_remaining / max_charge < 0.3 and charging_nodes:
                # Pick a charging station (for now, the first one)
                target_station = charging_nodes[0]

                recommendations.append({
                    "customerId": cust["id"],
                    "chargingRecommendations": [
                        {
                            "nodeId": target_station,
                            "chargeTo": 1.0
                        }
                    ]
                })

    return recommendations



def generate_tick(map_obj, current_tick):
    return {
        "tick": current_tick,
        "customerRecommendations": generate_customer_recommendations(map_obj, current_tick),
    }


def should_move_on_to_next_tick(response):
    # Always move on to the next tick unless you want to retry same tick on error
    return True


# --- Main Game Loop ---
def main():
    api_key = "028b69dd-01e9-4921-aa92-681e5ab24b62"  # If your server requires it
    base_url = "http://localhost:8080"
    map_name = "Turbohill"

    client = ConsiditionClient(base_url, api_key)

    # Fetch map data
    try:
        map_obj = client.get_map(map_name)
    except Exception as e:
        print(f"Failed to fetch map: {e}")
        sys.exit(1)

    if not map_obj:
        print("Failed to fetch map!")
        sys.exit(1)

    print(f"Loaded map: {map_obj.get('name', 'Unknown')} ({map_obj.get('dimX')}x{map_obj.get('dimY')})")

    final_score = 0
    good_ticks = []
    current_tick = generate_tick(map_obj, 0)
    input_payload = {
        "mapName": map_name,
        "ticks": [current_tick],
    }

    total_ticks = int(map_obj.get("ticks", 300))  # default to 300 if missing

    for i in range(total_ticks):
        while True:
            print(f"Playing tick: {i}")
            start = time.perf_counter()
            try:
                game_response = client.post_game(input_payload)
            except Exception as e:
                print(f"Error posting game data: {e}")
                sys.exit(1)

            elapsed_ms = (time.perf_counter() - start) * 1000
            print(f"Tick {i} took: {elapsed_ms:.2f}ms")

            if not game_response:
                print("Got no game response")
                sys.exit(1)

            # Extract score
            final_score = game_response.get("score", 0)
            print(f"Partial score at tick {i}: {final_score}")

            # Move to next tick
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

            # retry logic if needed
            updated_map = game_response.get("map", map_obj) or map_obj
            current_tick = generate_tick(updated_map, i)
            input_payload = {
                "mapName": map_name,
                "ticks": [*good_ticks, current_tick],
                "playToTick": i
            }

    print(f"\n✅ Final score: {final_score}")


if __name__ == "__main__":
    main()
