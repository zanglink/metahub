import requests
import random

# URL của API để tạo bot chèn quest
create_url = "https://dac-api.metahub.finance/eventRewardSettings/create"
api_key = "DAC-private-private-!!!"

# URL của API để lấy danh sách người dùng thực
get_users_url = "https://dac-api.metahub.finance/eventRewardSettings/realUsers"

# URL của API để thiết lập giải thưởng ngẫu nhiên
random_winner_url = "https://dac-api.metahub.finance/eventRewardSettings/randomWinner"

# Danh sách các quest ID để tạo
event_ids = [
    "666a9db589d65bf7ded1d607",
    "666aa1da89d65bf7ded1fa60"
]

# Cấu hình quest ID cùng với số lượng địa chỉ cần chọn
event_configurations = [
    {"event_id": "6662c4235500dc41aea967db", "count": 2}
]

# Hàm để tạo bot chèn quest
def create_event(event_id):
    payload = {"event": event_id}
    headers = {"Content-Type": "application/json"}
    params = {"key": api_key}
    response = requests.post(create_url, json=payload, params=params, headers=headers)
    
    if response.status_code == 200:
        print(f"Event {event_id} created successfully.")
        return response.json()
    else:
        print(f"Failed to create event {event_id}. Status code: {response.status_code}")
        print("Error message:", response.text)
        return None

# Hàm để lấy danh sách địa chỉ người dùng từ event ID
def get_addresses(event_id):
    params = {"key": api_key, "event": event_id}
    response = requests.get(get_users_url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            return [user['user']['address'] for user in data['data']]
        else:
            print(f"API response unsuccessful for event {event_id}.")
            return []
    else:
        print(f"Failed to fetch data for event {event_id}. Status code: {response.status_code}")
        print("Error message:", response.text)
        return []

# Hàm để chọn ngẫu nhiên các địa chỉ từ danh sách
def select_random_addresses(addresses, count):
    return random.sample(addresses, count) if len(addresses) >= count else addresses

# Hàm để thiết lập giải thưởng ngẫu nhiên cho các địa chỉ đã chọn
def set_random_winners(event_id, addresses):
    payload = {
        "event": event_id,
        "remainDistributeAll": False,
        "winnerAddresses": addresses
    }
    headers = {"Content-Type": "application/json"}
    response = requests.patch(random_winner_url, params={"key": api_key}, json=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            print(f"Successfully set random winners for event {event_id}.")
        else:
            print(f"Failed to set random winners for event {event_id}. Response was unsuccessful.")
            print("Error message:", data)
    else:
        print(f"Failed to set random winners for event {event_id}. Status code: {response.status_code}")
        print("Error message:", response.text)

# Hàm để xử lý các winner cho từng quest
def process_events(event_configurations):
    for config in event_configurations:
        event_id = config["event_id"]
        count = config["count"]
        
        addresses = get_addresses(event_id)
        if addresses:
            selected_addresses = select_random_addresses(addresses, count)
            print(f"Selected addresses for event {event_id}: {selected_addresses}")
            set_random_winners(event_id, selected_addresses)
        else:
            print(f"No addresses found for event {event_id}")

# Hàm để tạo bot chèn tất cả các quest trong danh sách
def create_all_events(event_ids):
    for event_id in event_ids:
        create_event(event_id)

# Hàm main
def main():
    # Tạo bot chèn các quest
    #create_all_events(event_ids)
    
    # Xử lý các event để chọn địa chỉ ngẫu nhiên và thiết lập giải thưởng
    process_events(event_configurations)

# Gọi hàm main
if __name__ == "__main__":
    main()
