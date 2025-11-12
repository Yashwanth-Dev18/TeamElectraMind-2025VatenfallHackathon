class GameState:
    def __init__(self, map_obj):
        self.map_obj = map_obj
        self.customers = map_obj.get('customers', [])
        self.zones = map_obj.get('zones', [])
        self.vehicles = map_obj.get('vehicles', [])
    
    def explore_game_state(self):
        """Understand what we're working with"""
        print("\n=== GAME STATE ANALYSIS ===")
        
        print(f"Total Customers: {len(self.customers)}")
        
        # Check personas
        personas = {}
        for customer in self.customers:
            persona = customer.get('persona', 'Unknown')
            personas[persona] = personas.get(persona, 0) + 1
        print("Persona distribution:", personas)
        
        print(f"Total Vehicles: {len(self.vehicles)}")
        print(f"Total Zones: {len(self.zones)}")
        
        for zone in self.zones:
            stations = zone.get('chargingStations', [])
            print(f"Zone {zone.get('id')} has {len(stations)} charging stations")
            for station in stations:
                print(f"  - Station {station.get('id')}: Type {station.get('type')}")

class GameResponse:
    def __init__(self, response):
        self.response = response
        self.score = response.get('score', 0)
        self.kwh_revenue = response.get('kwhRevenue', 0)
        self.completion_score = response.get('customerCompletionScore', 0)
        self.customer_scores = response.get('detailsCustomerScores', [])
    
    def debug(self):
        """Debug what's in the game response"""
        print("\n=== GAME RESPONSE DEBUG ===")
        print(f"Score: {self.score}")
        print(f"KWH Revenue: {self.kwh_revenue}")
        print(f"Customer Completion Score: {self.completion_score}")
        print(f"Customer scores: {len(self.customer_scores)}")
        for score in self.customer_scores:
            print(f"  Customer {score.get('customerId')}: {score.get('score', 0)}")