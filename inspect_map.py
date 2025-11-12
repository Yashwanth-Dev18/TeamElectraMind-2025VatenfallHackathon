from client import ConsiditionClient

def inspect_map():
    # For local testing, these values work
    api_key = "test-key"  # Can be anything for local
    base_url = "http://localhost:8080"
    map_name = "turbohill"  # Try this map first
    
    client = ConsiditionClient(base_url, api_key)
    
    try:
        print("=== INSPECTING MAP ===")
        
        # 1. Get map config (metadata)
        print("\n1. MAP CONFIG:")
        map_config = client.get_map_config(map_name)
        print(f"Map name: {map_name}")
        print(f"Total ticks: {map_config.get('ticks')}")
        print(f"Max cars: {map_config.get('maxCars')}")
        print(f"All config keys: {list(map_config.keys())}")
        
        # 2. Get full map data
        print("\n2. FULL MAP DATA:")
        full_map = client.get_map(map_name)
        
        # Basic counts
        print(f"Number of nodes: {len(full_map.get('nodes', []))}")
        print(f"Number of edges: {len(full_map.get('edges', []))}")
        print(f"Number of charging stations: {len(full_map.get('chargingStations', []))}")
        print(f"Number of customers: {len(full_map.get('customers', []))}")
        print(f"Number of cars: {len(full_map.get('cars', []))}")
        
        # Sample data
        print("\n3. SAMPLE DATA:")
        if full_map.get('nodes'):
            print(f"First node: {full_map['nodes'][0]}")
        if full_map.get('edges'):
            print(f"First edge: {full_map['edges'][0]}")
        if full_map.get('chargingStations'):
            print(f"First charging station: {full_map['chargingStations'][0]}")
        if full_map.get('customers'):
            print(f"First customer: {full_map['customers'][0]}")
        if full_map.get('cars'):
            print(f"First car: {full_map['cars'][0]}")
            
    except Exception as e:
        print(f"Failed to inspect map: {e}")

if __name__ == "__main__":
    inspect_map()