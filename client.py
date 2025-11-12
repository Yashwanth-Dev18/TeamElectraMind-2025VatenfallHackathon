import requests

class ConsiditionClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {"x-api-key": self.api_key}
    
    def get_map_config(self, map_name: str):
        return self.request("GET", "/api/map-config", params={"mapName": map_name})

    def get_map(self, map_name: str):
        return self.request("GET", "/api/map", params={"mapName": map_name})
    
    def post_game(self, data: object):
        return self.request("POST", "/api/game", json=data)

    def request(self, method: str, endpoint: str, **kwargs):
        url = f"{self.base_url}{endpoint}"
        try:
            # For cloud API (HTTPS), remove verify=False
            # For local Docker, you might need verify=False
            if "localhost" in self.base_url:
                response = requests.request(method, url, headers=self.headers, verify=False, **kwargs)
            else:
                response = requests.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making request to {url}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Error response status: {e.response.status_code}")
                print(f"Error response body: {e.response.text}")
            raise