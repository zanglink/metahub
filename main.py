import requests
import random
import tkinter as tk
from tkinter import simpledialog

# URL của API để tạo bot chèn quest
create_url = "https://dac-api.metahub.finance/eventRewardSettings/create"
api_key = "DAC-private-private-!!!"

# URL của API dừng việc chèn bot vào quest
stop_add_bot_url = "https://dac-api.metahub.finance/eventRewardSettings/deactive"

# URL của API để lấy danh sách người dùng thực
get_users_url = "https://dac-api.metahub.finance/eventRewardSettings/realUsers"

# URL của API để thiết lập giải thưởng ngẫu nhiên
random_winner_url = "https://dac-api.metahub.finance/eventRewardSettings/randomWinner"

# URL của API để chèn bot ngẫu nhiên
add_bot_url = "https://dac-server-dev.metahub.finance/events/addBot"

# Cấu hình quest ID cùng với số lượng địa chỉ cần chọn
event_configurations = [
    {"event_id": "666a974989d65bf7ded197c1", "count": 800},
    {"event_id": "666a995389d65bf7ded1a84d", "count": 1000},
    {"event_id": "666a9c7589d65bf7ded1c520", "count": 1000},
    {"event_id": "666a9db589d65bf7ded1d607", "count": 400},
    {"event_id": "666aa1da89d65bf7ded1fa60", "count": 300},
    {"event_id": "66739b58bbf2b16c06c5dafc", "count": 200},
    {"event_id": "6673a10fbbf2b16c06c69564", "count": 200},
    {"event_id": "6662c6575500dc41aea97e3e", "count": 500}
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

# Hàm dừng việc chèn bot
def stop_add_bot(event_id):
    payload = {
        "event": event_id,
        "status": True
    }
    headers = {
        "Content-Type": "application/json"
    }
    params = {
        "key": api_key
    }
    response = requests.patch(stop_add_bot_url, json=payload, params=params, headers=headers)
    
    if response.status_code == 200:
        print(f"Successfully stopped adding bot for event {event_id}.")
    else:
        print(f"Failed to stop adding bot for event {event_id}. Status code: {response.status_code}")
        print("Error message:", response.text)

# Hàm để tạo bot chèn tất cả các quest trong danh sách
def create_all_events(event_configurations):
    for config in event_configurations:
        create_event(config["event_id"])

def stop_add_bot_all_events(event_configurations):
    for config in event_configurations:
        stop_add_bot(config["event_id"])

# Hàm để chèn bot ngẫu nhiên vào các quest
def add_random_bot(event_id, quantity):
    payload = {
        "event": event_id,
        "quantity": quantity,
        "isContainWeb2": False
    }
    headers = {
        "Content-Type": "application/json"
    }
    params = {
        "key": api_key
    }
    response = requests.post(add_bot_url, json=payload, params=params, headers=headers)
    
    if response.status_code == 200:
        print(f"Successfully added {quantity} bots to event {event_id}.")
    else:
        print(f"Failed to add bots to event {event_id}. Status code: {response.status_code}")
        print("Error message:", response.text)

def add_random_bot_all_events(event_configurations):
    for config in event_configurations:
        add_random_bot(config["event_id"], config["count"])

# Hàm để hỏi người dùng lựa chọn hành động
def ask_user_action():
    root = tk.Tk()
    root.withdraw()
    action = simpledialog.askinteger("Input", "Choose action: 1 for Create All Events, 2 for Stop Add Bot All Events, 3 for Process Events, 4 for Add Random Bot All Events")
    if action == 1:
        create_all_events(event_configurations)
    elif action == 2:
        stop_add_bot_all_events(event_configurations)
    elif action == 3:
        process_events(event_configurations)
    elif action == 4:
        add_random_bot_all_events(event_configurations)
    else:
        print("Invalid action")

# Hàm main
def main():
    ask_user_action()

# Gọi hàm main
if __name__ == "__main__":
    main()
