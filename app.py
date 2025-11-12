import os
import sys
import time
from dotenv import load_dotenv
from client import ConsiditionClient
from game_state import GameState, GameResponse
from algorithm import ChargingAlgorithm, PersonaAwareAlgorithm

def main():
    # Load configuration
    load_dotenv()
    api_key = os.getenv("API_KEY")
    base_url = "http://localhost:8080"
    map_name = "Turbohill"

    print(f"Starting game with API Key: {api_key}")

    # Initialize components
    client = ConsiditionClient(base_url, api_key)
    
    # Choose your algorithm strategy
    # algorithm = ChargingAlgorithm()  # Basic strategy
    algorithm = PersonaAwareAlgorithm()  # More advanced strategy
    
    print(f"Using algorithm: {algorithm.strategy_name}")

    try:
        # Get map and initialize game state
        map_obj = client.get_map(map_name)
        print("Successfully loaded map!")
        
        game_state = GameState(map_obj)
        game_state.explore_game_state()
        
    except Exception as e:
        print(f"Failed to fetch map: {e}")
        sys.exit(1)

    # Test with small number of ticks first
    test_ticks = 20
    
    final_score = 0
    good_ticks = []

    # Generate first tick
    current_tick = algorithm.generate_tick(game_state, 0)
    input_payload = {
        "mapName": map_name,
        "ticks": [current_tick],
    }

    print(f"\n=== STARTING SIMULATION ({test_ticks} ticks) ===")

    # Main game loop
    for i in range(test_ticks):
        while True:
            print(f"\n--- Playing tick: {i} ---")
            start = time.perf_counter()
            
            try:
                raw_response = client.post_game(input_payload)
                game_response = GameResponse(raw_response)
            except Exception as e:
                print(f"Error posting game data: {e}")
                sys.exit(1)
                
            elapsed_ms = (time.perf_counter() - start) * 1000
            print(f"Tick {i} took: {elapsed_ms:.2f}ms")

            # Debug the response
            game_response.debug()

            final_score = game_response.score

            if algorithm.should_move_on_to_next_tick(game_response):
                good_ticks.append(current_tick)
                updated_map = raw_response.get("map", map_obj) or map_obj
                game_state = GameState(updated_map)
                current_tick = algorithm.generate_tick(game_state, i + 1)
                input_payload = {
                    "mapName": map_name,
                    "playToTick": i + 1,
                    "ticks": [*good_ticks, current_tick],
                }
                break

            # If we need to retry this tick (should_move_on_to_next_tick returns False)
            updated_map = raw_response.get("map", map_obj) or map_obj
            game_state = GameState(updated_map)
            current_tick = algorithm.generate_tick(game_state, i)
            input_payload = {
                "mapName": map_name,
                "playToTick": i,
                "ticks": [*good_ticks, current_tick],
            }

    print(f"\n=== FINAL RESULT ===")
    print(f"Final score after {test_ticks} ticks: {final_score}")

if __name__ == "__main__":
    main()