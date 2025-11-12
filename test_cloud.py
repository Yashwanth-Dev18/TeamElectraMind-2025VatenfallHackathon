from client import ConsiditionClient

def test_cloud_connection():
    api_key = "4c516391-366c-4909-9a3a-bbeb2de63358"
    base_url = "https://api.considition.com"
    map_name = "turbohill"
    
    client = ConsiditionClient(base_url, api_key)
    
    try:
        print("Testing connection to cloud API...")
        
        # Try to get map config
        map_config = client.get_map_config(map_name)
        print(f"✅ Connected successfully!")
        print(f"Map: {map_name}")
        print(f"Total ticks: {map_config.get('ticks')}")
        print(f"Max cars: {map_config.get('maxCars')}")
        
        # Try to get full map
        full_map = client.get_map(map_name)
        print(f"Nodes: {len(full_map.get('nodes', []))}")
        print(f"Edges: {len(full_map.get('edges', []))}")
        print(f"Charging stations: {len(full_map.get('chargingStations', []))}")
        print(f"Customers: {len(full_map.get('customers', []))}")
        print(f"Cars: {len(full_map.get('cars', []))}")
        
        # Show sample customer
        if full_map.get('customers'):
            customer = full_map['customers'][0]
            print(f"\nSample customer:")
            print(f"  ID: {customer.get('id')}")
            print(f"  State: {customer.get('state')}")
            print(f"  Persona: {customer.get('persona')}")
            print(f"  Destination: {customer.get('destinationNodeId')}")
            
    except Exception as e:
        print(f"❌ Failed to connect: {e}")

if __name__ == "__main__":
    test_cloud_connection()