import requests
import random
import tkinter as tk
from tkinter import ttk, messagebox

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
add_bot_url = "https://dac-api.metahub.finance/events/addBot"

# Biến để lưu kết quả
results = []

# Hàm để tạo bot chèn quest
def create_event(event_id):
    payload = {"event": event_id}
    headers = {"Content-Type": "application/json"}
    params = {"key": api_key}
    response = requests.post(create_url, json=payload, params=params, headers=headers)
    
    if response.status_code == 200:
        results.append(f"Event {event_id} created successfully.")
        return response.json()
    else:
        results.append(f"Failed to create event {event_id}. Status code: {response.status_code}")
        results.append(f"Error message: {response.text}")
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
            results.append(f"API response unsuccessful for event {event_id}.")
            return []
    else:
        results.append(f"Failed to fetch data for event {event_id}. Status code: {response.status_code}")
        results.append(f"Error message: {response.text}")
        return []

# Hàm để chọn ngẫu nhiên các địa chỉ từ danh sách
def select_random_addresses(addresses, count):
    return random.sample(addresses, count) if len(addresses) >= count else addresses

def replace_addresses(address_a, address_b):
    if not address_a:
        return address_b
    
    addresses_to_replace = list(set(address_a) - set(address_b))
    num_to_replace = min(len(addresses_to_replace), len(address_b))
    indexes_to_replace = random.sample(range(len(address_b)), num_to_replace)
    
    for i, index in enumerate(indexes_to_replace):
        address_b[index] = addresses_to_replace[i]
    
    return address_b

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
            results.append(f"Successfully set random winners for event {event_id}.")
        else:
            results.append(f"Failed to set random winners for event {event_id}. Response was unsuccessful.")
            results.append(f"Error message: {data}")
    else:
        results.append(f"Failed to set random winners for event {event_id}. Status code: {response.status_code}")
        results.append(f"Error message: {response.text}")

# Hàm để xử lý các winner cho từng quest
def process_events(event_configurations):
    for config in event_configurations:
        event_id = config["event_id"]
        count = config["count"]
        
        # Lấy địa chỉ thêm từ cấu hình (nếu có)
        additional_addresses = config.get("addresses", [])
        
        print(f"additional_addresses: {additional_addresses}")
        
        addresses = get_addresses(event_id)
        if addresses:
            # Thêm địa chỉ thêm vào danh sách địa chỉ
            addresses.extend(additional_addresses)
            selected_addresses = select_random_addresses(addresses, count)
            replace_addresses(additional_addresses, selected_addresses)
            results.append(f"Selected addresses for event {event_id}: {selected_addresses}")
            set_random_winners(event_id, selected_addresses)
        else:
            results.append(f"No addresses found for event {event_id}")

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
        results.append(f"Successfully stopped adding bot for event {event_id}.")
    else:
        results.append(f"Failed to stop adding bot for event {event_id}. Status code: {response.status_code}")
        results.append(f"Error message: {response.text}")

# Hàm để tạo bot chèn tất cả các quest trong danh sách
def create_all_events(event_configurations):
    for config in event_configurations:
        create_event(config["event_id"])

def stop_add_bot_all_events(event_configurations):
    for config in event_configurations:
        stop_add_bot(config["event_id"])

# Hàm để chèn bot ngẫu nhiên
def add_random_bot(event_id, count):
    payload = {
        "event": event_id,
        "quantity": count,
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
        results.append(f"Successfully added random bot for event {event_id}.")
    else:
        results.append(f"Failed to add random bot for event {event_id}. Status code: {response.status_code}")
        results.append(f"Error message: {response.text}")

def add_random_bot_all_events(event_configurations):
    for config in event_configurations:
        add_random_bot(config["event_id"], config["count"])

# Hàm để hỏi người dùng lựa chọn hành động và nhập cấu hình
def ask_user_action():
    root = tk.Tk()
    root.title("Choose Action")
    root.geometry("600x400")
    root.configure(bg="#f0f0f0")
    root.resizable(False, False)

    action = tk.IntVar()

    label = tk.Label(root, text="Choose action:", bg="#f0f0f0", font=("Helvetica", 14))
    label.pack(pady=10)

    style = ttk.Style()
    style.configure("TRadiobutton", background="#f0f0f0", font=("Helvetica", 12))

    actions_frame = tk.Frame(root, bg="#f0f0f0")
    actions_frame.pack(pady=10)

    ttk.Radiobutton(actions_frame, text="Create Bot On Top All Events", variable=action, value=1).pack(anchor=tk.W)
    ttk.Radiobutton(actions_frame, text="Stop Add Bot All Events", variable=action, value=2).pack(anchor=tk.W)
    ttk.Radiobutton(actions_frame, text="Random Winner All Events", variable=action, value=3).pack(anchor=tk.W)
    ttk.Radiobutton(actions_frame, text="Add Random Bot All Events", variable=action, value=4).pack(anchor=tk.W)

    config_label = tk.Label(root, text="Enter event configurations:", bg="#f0f0f0", font=("Helvetica", 14))
    config_label.pack(pady=10)

    config_input = tk.Text(root, height=5, width=40)
    config_input.pack(pady=10)
    
    def on_submit():
        config_data = config_input.get("1.0", tk.END).strip()
        global event_configurations, results
        event_configurations = []
        results = []
        for line in config_data.split('\n'):
            if line:
                parts = line.split(',')
                event_id = parts[0].strip()
                count = int(parts[1].strip()) if len(parts) > 1 else 0
                addresses = [addr.strip() for addr in parts[2:]] if len(parts) > 2 else []
                event_configurations.append({"event_id": event_id, "count": count, "addresses": addresses})

        
        if action.get() == 1:
            create_all_events(event_configurations)
        elif action.get() == 2:
            stop_add_bot_all_events(event_configurations)
        elif action.get() == 3:
            process_events(event_configurations)
        elif action.get() == 4:
            add_random_bot_all_events(event_configurations)
        else:
            results.append("Invalid action")
        
        show_results()
        root.quit()

    submit_button = tk.Button(root, text="Submit", command=on_submit, bg="#4CAF50", fg="white", font=("Helvetica", 12), width=15)
    submit_button.pack(pady=10)

    root.mainloop()

# Hàm để hiển thị kết quả sau khi hoàn thành các hành động
def show_results():
    result_window = tk.Tk()
    result_window.title("Results")
    result_window.geometry("600x400")
    result_window.configure(bg="#f0f0f0")
    result_window.resizable(False, False)

    result_text = tk.Text(result_window, wrap=tk.WORD, bg="#f0f0f0", font=("Helvetica", 12))
    result_text.pack(pady=10, padx=10)

    for result in results:
        result_text.insert(tk.END, result + "\n")

    close_button = tk.Button(result_window, text="Close", command=result_window.destroy, bg="#4CAF50", fg="white", font=("Helvetica", 12), width=15)
    close_button.pack(pady=10)

    result_window.mainloop()

# Chạy chương trình
ask_user_action()
