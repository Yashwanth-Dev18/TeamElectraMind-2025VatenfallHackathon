import sys
import time
from client import ConsiditionClient

def should_move_on_to_next_tick(response):
    return True

def generate_customer_recommendations(map_obj, current_tick):
    """
    THIS IS WHERE YOUR ALGORITHM GOES!
    Analyze the map and make decisions about which customers to serve.
    """
    recommendations = []
    
    # Get available customers
    customers = map_obj.get("customers", [])
    
    # Simple strategy: accept all available customers
    for customer in customers:
        if customer.get("state") == "Home":  # Only accept new customers
            recommendations.append({
                "customerId": customer["id"],
                "recommendation": "ACCEPT",
                "destinationNodeId": customer["destinationNodeId"]
            })
    
    return recommendations

def generate_tick(map_obj, current_tick):
    return {
        "tick": current_tick,
        "customerRecommendations": generate_customer_recommendations(map_obj, current_tick),
    }

def main():
    # FOR CLOUD API (Real competition - updates leaderboard)
    api_key = "4c516391-366c-4909-9a3a-bbeb2de63358"
    base_url = "https://api.considition.com"
    map_name = "turbohill"  # First training map
    
    # FOR LOCAL TESTING (comment above and uncomment below)
    # api_key = "test-key"
    # base_url = "http://localhost:8080"
    # map_name = "turbohill"
    
    client = ConsiditionClient(base_url, api_key)

    try:
        print(f"Fetching map: {map_name}")
        map_obj = client.get_map(map_name)
        print("✅ Map fetched successfully!")
    except Exception as e:
        print(f"❌ Failed to fetch map: {e}")
        sys.exit(1)

    if not map_obj:
        print("❌ Failed to fetch map!")
        sys.exit(1)

    final_score = 0
    good_ticks = []

    current_tick = generate_tick(map_obj, 0)
    input_payload = {
        "mapName": map_name,
        "ticks": [current_tick],
    }

    total_ticks = int(map_obj.get("ticks", 288))  # Default to 288 if not found
    
    print(f"Starting simulation for {total_ticks} ticks...")

    for i in range(total_ticks):
        while True:
            print(f"Playing tick: {i}")
            start = time.perf_counter()
            try:
                game_response = client.post_game(input_payload)
            except Exception as e:
                print(f"❌ Error posting game data: {e}")
                sys.exit(1)
            elapsed_ms = (time.perf_counter() - start) * 1000
            print(f"Tick {i} took: {elapsed_ms:.2f}ms")

            if not game_response:
                print("❌ Got no game response")
                sys.exit(1)

            # Update score
            final_score = game_response.get("score", 0)
            print(f"Current score: {final_score}")

            if should_move_on_to_next_tick(game_response):
                good_ticks.append(current_tick)
                updated_map = game_response.get("map", map_obj) or map_obj
                current_tick = generate_tick(updated_map, i + 1)
                input_payload = {
                    "mapName": map_name,
                    "playToTick": i + 1,
                    "ticks": [*good_ticks, current_tick],
                }
                break

            updated_map = game_response.get("map", map_obj) or map_obj
            current_tick = generate_tick(updated_map, i)
            input_payload = {
                "mapName": map_name,
                "playToTick": i,
                "ticks": [*good_ticks, current_tick],
            }

    print(f"🎯 Final score: {final_score}")

if __name__ == "__main__":
    main()