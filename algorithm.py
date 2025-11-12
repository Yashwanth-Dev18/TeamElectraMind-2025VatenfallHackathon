from game_state import GameState

class ChargingAlgorithm:
    def __init__(self):
        self.strategy_name = "Basic Low Battery Charging"
    
    def should_move_on_to_next_tick(self, game_response):
        return True
    
    def generate_customer_recommendations(self, game_state, current_tick):
        """Basic strategy: recommend charging for customers with low battery"""
        recommendations = []
        
        print(f"Tick {current_tick}: Checking {len(game_state.customers)} customers...")
        
        for customer in game_state.customers:
            customer_id = customer.get('id')
            current_charge = customer.get('currentCharge', 0)
            battery_capacity = customer.get('batteryCapacity', 100)
            
            # Calculate battery percentage
            battery_percentage = (current_charge / battery_capacity) * 100 if battery_capacity > 0 else 0
            
            print(f"  Customer {customer_id}: {battery_percentage:.1f}% charge, Persona: {customer.get('persona')}")
            
            # If battery is below 50%, try to charge
            if battery_percentage < 50:
                # Find available charging stations
                for zone in game_state.zones:
                    for station in zone.get('chargingStations', []):
                        # Recommend this station
                        recommendations.append({
                            'customerId': customer_id,
                            'zoneId': zone.get('id'),
                            'chargingStationId': station.get('id')
                        })
                        print(f"    → Recommending charging at Zone {zone.get('id')}, Station {station.get('id')}")
                        break  # Only recommend one station per customer
                    break  # Only use first zone for now
                    
        print(f"  Making {len(recommendations)} total recommendations")
        return recommendations
    
    def generate_tick(self, game_state, current_tick):
        return {
            "tick": current_tick,
            "customerRecommendations": self.generate_customer_recommendations(game_state, current_tick),
        }

# You can create different algorithm strategies later
class PersonaAwareAlgorithm(ChargingAlgorithm):
    def __init__(self):
        super().__init__()
        self.strategy_name = "Persona-Aware Charging"
    
    def generate_customer_recommendations(self, game_state, current_tick):
        """More sophisticated strategy considering customer personas"""
        recommendations = []
        
        print(f"Tick {current_tick}: Persona-aware strategy checking {len(game_state.customers)} customers...")
        
        for customer in game_state.customers:
            customer_id = customer.get('id')
            current_charge = customer.get('currentCharge', 0)
            battery_capacity = customer.get('batteryCapacity', 100)
            persona = customer.get('persona', 'Neutral')
            
            battery_percentage = (current_charge / battery_capacity) * 100 if battery_capacity > 0 else 0
            
            print(f"  Customer {customer_id}: {battery_percentage:.1f}% charge, Persona: {persona}")
            
            # Different charging thresholds based on persona
            charging_threshold = self.get_charging_threshold(persona)
            
            if battery_percentage < charging_threshold:
                best_station = self.find_best_station(game_state, customer)
                if best_station:
                    recommendations.append(best_station)
                    print(f"    → Recommending charging at Zone {best_station['zoneId']}, Station {best_station['chargingStationId']}")
                    
        print(f"  Making {len(recommendations)} total recommendations")
        return recommendations
    
    def get_charging_threshold(self, persona):
        """Different personas have different charging preferences"""
        thresholds = {
            'CostSensitive': 20,   # Wait longer to charge (cheaper?)
            'EcoConscious': 40,    # Charge earlier to use green energy
            'Stressed': 60,        # Charge more frequently to avoid stress
            'DislikesDriving': 50, # Neutral preference
            'Neutral': 40          # Default
        }
        return thresholds.get(persona, 40)
    
    def find_best_station(self, game_state, customer):
        """Find the best charging station for this customer"""
        # For now, just return the first available station
        # Later you can implement logic for green stations, zone capacity, etc.
        for zone in game_state.zones:
            for station in zone.get('chargingStations', []):
                return {
                    'customerId': customer.get('id'),
                    'zoneId': zone.get('id'),
                    'chargingStationId': station.get('id')
                }
        return None