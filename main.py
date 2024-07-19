import requests
import json
import random
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from datetime import datetime

# URLs and API key
API_KEY = "DAC-private-private-!!!"
BASE_URL = "https://dac-api.metahub.finance/eventRewardSettings/"
EVENT_URL = "https://dac-api.metahub.finance/events/"
COMMUNITY_URL = "https://dac-api.metahub.finance/communities/"
CREATE_URL = f"{BASE_URL}create"
STOP_ADD_BOT_URL = f"{BASE_URL}deactive"
GET_USERS_URL = f"{BASE_URL}realUsers"
RANDOM_WINNER_URL = f"{BASE_URL}randomWinner"
ADD_BOT_URL = f"{EVENT_URL}addBot"
REFUND_REWARD_URL = f"{BASE_URL}refundReward"
EDIT_USER_COMMUNITY_URL = f"{COMMUNITY_URL}private/manager"
CHECK_POINT = f"{EVENT_URL}private/userPoint"

# Results storage
results = []

def create_event(event_id):
    payload = {"event": event_id}
    response = requests.post(CREATE_URL, json=payload, params={"key": API_KEY}, headers={"Content-Type": "application/json"})
    
    if response.status_code == 200:
        results.append(f"Event {event_id} created successfully.")
        return response.json()
    else:
        results.append(f"Failed to create event {event_id}. Status code: {response.status_code}")
        results.append(f"Error message: {response.text}")
        return None

def get_addresses(event_id):
    response = requests.get(GET_USERS_URL, params={"key": API_KEY, "event": event_id})
    
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

def filter_addresses(list_address_a, list_address_b):
    return [address for address in list_address_a if address in list_address_b]

def set_random_winners(event_id, addresses):
    payload = {
        "event": event_id,
        "remainDistributeAll": False,
        "winnerAddresses": addresses
    }
    response = requests.patch(RANDOM_WINNER_URL, params={"key": API_KEY}, json=payload, headers={"Content-Type": "application/json"})
    
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

def process_events(event_configurations):
    for config in event_configurations:
        event_id = config["event_id"]
        count = config["count"]
        additional_addresses = config.get("addresses", [])
        addresses = get_addresses(event_id)
        if addresses:
            selected_addresses = select_random_addresses(addresses, count)
            filtered_address_a = filter_addresses(additional_addresses, addresses)
            selected_addresses = replace_addresses(filtered_address_a, selected_addresses)
            results.append(f"Selected addresses for event {event_id}: {selected_addresses}")
            set_random_winners(event_id, selected_addresses)
        else:
            results.append(f"No addresses found for event {event_id}")

def stop_add_bot(event_id):
    payload = {"event": event_id, "status": True}
    response = requests.patch(STOP_ADD_BOT_URL, json=payload, params={"key": API_KEY}, headers={"Content-Type": "application/json"})
    
    if response.status_code == 200:
        results.append(f"Successfully stopped adding bot for event {event_id}.")
    else:
        results.append(f"Failed to stop adding bot for event {event_id}. Status code: {response.status_code}")
        results.append(f"Error message: {response.text}")

def create_all_events(event_configurations):
    for config in event_configurations:
        create_event(config["event_id"])

def stop_add_bot_all_events(event_configurations):
    for config in event_configurations:
        stop_add_bot(config["event_id"])

def add_random_bot(event_id, count):
    chunk_size = 10
    num_chunks = (count + chunk_size - 1) // chunk_size
    
    for _ in range(num_chunks):
        current_chunk_size = min(chunk_size, count)
        payload = {"event": event_id, "quantity": current_chunk_size, "isContainWeb2": False}
        response = requests.post(ADD_BOT_URL, json=payload, params={"key": API_KEY}, headers={"Content-Type": "application/json"})
        
        if response.status_code == 200:
            results.append(f"Successfully added {current_chunk_size} random bots for event {event_id}.")
        else:
            results.append(f"Failed to add {current_chunk_size} random bots for event {event_id}. Status code: {response.status_code}")
            results.append(f"Error message: {response.text}")
        
        count -= current_chunk_size


def add_random_bot_all_events(event_configurations):
    for config in event_configurations:
        add_random_bot(config["event_id"], config["count"])

def format_date(date_str):
    return datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y-%m-%dT00:00:00.000Z')

def export_refund_reward_to_excel(event, from_date, to_date, type_token):
    params = {
        "from": format_date(from_date),
        "to": format_date(to_date),
        "key": API_KEY
    }
    
    if event:
        params["events"] = event
    
    response = requests.get(REFUND_REWARD_URL, params=params)
    
    if response.status_code == 200:
        try:
            data = response.json().get('data', [])
            if data:
                rows = []
                for event_data in data:
                    token = event_data.get('token', '')
                    if type_token == "MEN" and token == "MEN":
                        continue
                    elif type_token != "MEN" and token != "MEN":
                        continue

                    event_id = event_data.get('event', '')
                    event_title = event_data.get('title', '')
                    chain = event_data.get('chain', '')
                    top_bonus = event_data.get('topBonusNumber', 0)
                    random_bonus = event_data.get('randomBonusNumber', 0)
                    total_fund_amount = event_data.get('totalFundTokenAmount', 0)
                    total_refund_amount = event_data.get('totalRefundAmount', 0)
                    total_user_reward = event_data.get('totalUserReward', 0)
                    total_bot_refund = event_data.get('totalBotRefund', 0)
                    
                    random_winners = [user['address'] for user in event_data.get('randomWinnerUsers', [])]
                    random_winners_str = ", ".join(random_winners)
                    
                    rows.append({
                        'Event ID': event_id,
                        'Event Title': event_title,
                        'Token': token,
                        'Chain': chain,
                        'Top Bonus Number': top_bonus,
                        'Random Bonus Number': random_bonus,
                        'Total Fund Token Amount': total_fund_amount,
                        'Total Refund Amount': total_refund_amount,
                        'Total User Reward': total_user_reward,
                        'Total Bot Refund': total_bot_refund,
                        'Random Winner Addresses': random_winners_str
                    })
                
                df = pd.DataFrame(rows)
                file_name = f"refund_reward_{event or 'all_events'}_{from_date}_{to_date}.xlsx"
                df.to_excel(file_name, index=False)
                
                results.append(f"Data has been saved to {file_name}")
            else:
                results.append("No data found for the given parameters.")
        except Exception as e:
            results.append(f"Error processing data: {str(e)}")
    else:
        results.append(f"Failed to fetch refund reward data. Status code: {response.status_code}")
        results.append(f"Error message: {response.text}")

def export_random_winners_to_excel(event, from_date, to_date, type_token):
    params = {
        "from": format_date(from_date),
        "to": format_date(to_date),
        "key": API_KEY
    }
    
    if event:
        params["events"] = event
    
    response = requests.get(REFUND_REWARD_URL, params=params)
    
    if response.status_code == 200:
        try:
            data = response.json().get('data', [])
            if data:
                rows = []
                counter = 1  # Initialize the counter
                for event_data in data:
                    token = event_data.get('token', '')
                    if type_token == "MEN" and token != "MEN":
                        continue
                    elif type_token != "MEN" and token == "MEN":
                        continue

                    event_id = event_data.get('event', '')
                    random_bonus = event_data.get('randomBonusNumber', 0)
                    random_winners = [user['address'] for user in event_data.get('randomWinnerUsers', [])]

                    for winner in random_winners:
                        rows.append({
                            '#': counter,  # Add the counter value
                            'Event ID': event_id,
                            'Random Winner Address': winner,
                            'Token': token,
                            'Random Bonus Number': random_bonus
                        })
                        counter += 1  # Increment the counter for each winner
                
                df = pd.DataFrame(rows)
                file_name = f"random_winners_{event or 'all_events'}_{from_date}_{to_date}.xlsx"
                df.to_excel(file_name, index=False)
                
                print(f"Data has been saved to {file_name}")
            else:
                print("No data found for the given parameters.")
        except Exception as e:
            print(f"Error processing data: {str(e)}")
    else:
        print(f"Failed to fetch refund reward data. Status code: {response.status_code}")
        print(f"Error message: {response.text}")

def export_address_counts_to_excel(event_configurations):
    event_ids = [event['event_id'] for event in event_configurations]
    data = []

    for event_id in event_ids:
        response = requests.get(GET_USERS_URL, params={"key": API_KEY, "event": event_id})
        
        if response.status_code == 200:
            data_response = response.json()
            if data_response['success']:
                address_count = len([user['user']['address'] for user in data_response['data']])
                data.append({'#': len(data) + 1, 'event_id': event_id, 'count': address_count})
            else:
                results.append(f"API response unsuccessful for event {event_id}.")
        else:
            results.append(f"Failed to fetch data for event {event_id}. Status code: {response.status_code}")
            results.append(f"Error message: {response.text}")

    if data:
        df = pd.DataFrame(data)
        file_name = "address_counts.xlsx"
        df.to_excel(file_name, index=False)
        results.append(f"Data has been saved to {file_name}")
    else:
        results.append("No data to export.")

def edit_manager_to_community(user, community, action):
    payload = {
        "user": user,
        "community": community
    }
    if action == "add":
        response = requests.post(EDIT_USER_COMMUNITY_URL, json=payload, params={"key": API_KEY}, headers={"Content-Type": "application/json"})
    else:
        response = requests.delete(EDIT_USER_COMMUNITY_URL, json=payload, params={"key": API_KEY}, headers={"Content-Type": "application/json"})

    if response.status_code == 200:
        data = response.json()
        if data['success']:
            results.append(f"Successfully edited manager {user} to community {community}.")
        else:
            results.append(f"Failed to edit manager {user} to community {community}. Response was unsuccessful.")
            results.append(f"Error message: {data}")
    else:
        results.append(f"Failed to edit manager {user} to community {community}. Status code: {response.status_code}")
        results.append(f"Error message: {response.text}")

def check_point_user(user, event_id):
    payload = {
        "user": user,
        "event": event_id,
        "key": API_KEY
    }
    response = requests.get(CHECK_POINT, params=payload, headers={"Content-Type": "application/json"})
    
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            points = data.get('points', 'No points information available')
            result_data = {
                "user": user,
                "event": event_id,
                "points": points
            }
            file_name = f"user_points_{user}_{event_id}.json"
            with open(file_name, 'w') as f:
                json.dump(result_data, f, indent=4)
            messagebox.showinfo("Success", f"Data has been saved to {file_name}")
        else:
            messagebox.showerror("Error", f"Failed to retrieve points. Response was unsuccessful.\n{data}")
    else:
        messagebox.showerror("Error", f"Failed to retrieve points. Status code: {response.status_code}\n{response.text}")


def ask_user_action():
    root = tk.Tk()
    root.title("Choose Action")
    root.geometry("600x700")
    root.configure(bg="#f0f0f0")
    root.resizable(False, False)

    action = tk.IntVar()

    label = tk.Label(root, text="Choose action:", bg="#f0f0f0", font=("Helvetica", 14))
    label.pack(pady=10)

    style = ttk.Style()
    style.configure("TRadiobutton", background="#f0f0f0", font=("Helvetica", 12))

    # Frames for different action groups
    event_actions_frame = tk.LabelFrame(root, text="Action to Event", bg="#f0f0f0", font=("Helvetica", 14), padx=10, pady=10)
    event_actions_frame.pack(pady=10, fill="x")

    excel_actions_frame = tk.LabelFrame(root, text="Result to Excel", bg="#f0f0f0", font=("Helvetica", 14), padx=10, pady=10)
    excel_actions_frame.pack(pady=10, fill="x")

    community_actions_frame = tk.LabelFrame(root, text="Action to Community", bg="#f0f0f0", font=("Helvetica", 14), padx=10, pady=10)
    community_actions_frame.pack(pady=10, fill="x")

    def update_placeholder(*args):
        placeholder_text = {
            1: "event_id",
            2: "event_id",
            3: "event_id, number, address_setup",
            4: "event_id, count",
            5: "event, from, to, token",
            6: "user, community", 
            7: "user, community",
            8: "user, event_id",
            9: "event, from, to, token",
            10: "event_id"
        }.get(action.get(), "")
        config_input.delete("1.0", tk.END)
        config_input.insert("1.0", placeholder_text)

    action.trace("w", update_placeholder)

    # Event Actions
    ttk.Radiobutton(event_actions_frame, text="Create Bot On Top All Events", variable=action, value=1).pack(anchor=tk.W)
    ttk.Radiobutton(event_actions_frame, text="Stop Add Bot All Events", variable=action, value=2).pack(anchor=tk.W)
    ttk.Radiobutton(event_actions_frame, text="Random Winner All Events", variable=action, value=3).pack(anchor=tk.W)
    ttk.Radiobutton(event_actions_frame, text="Add Random Bot All Events", variable=action, value=4).pack(anchor=tk.W)

    # Excel Actions
    ttk.Radiobutton(excel_actions_frame, text="Check Point User", variable=action, value=8).pack(anchor=tk.W)
    ttk.Radiobutton(excel_actions_frame, text="Export refund Reward to Excel", variable=action, value=5).pack(anchor=tk.W)
    ttk.Radiobutton(excel_actions_frame, text="Export Random Winner to Excel", variable=action, value=9).pack(anchor=tk.W)
    ttk.Radiobutton(excel_actions_frame, text="Export Address Count to Excel", variable=action, value=10).pack(anchor=tk.W)

    # Community Actions
    ttk.Radiobutton(community_actions_frame, text="Add manager to Community", variable=action, value=6).pack(anchor=tk.W)
    ttk.Radiobutton(community_actions_frame, text="Delete manager to Community", variable=action, value=7).pack(anchor=tk.W)

    config_label = tk.Label(root, text="Enter event configurations:", bg="#f0f0f0", font=("Helvetica", 14))
    config_label.pack(pady=10)

    config_input = tk.Text(root, height=5, width=40)
    config_input.pack(pady=10)
    def on_submit():
        config_data = config_input.get("1.0", tk.END).strip()
        global event_configurations, results
        event_configurations = []
        results = []
        
        config_parts = config_data.split(',')

        if action.get() in [5, 9]:
            if len(config_parts) != 4:
                messagebox.showerror("Input Error", "Please provide event, from, to dates, and token type in the format 'event, from, to, token_type'.")
                return

            event = config_parts[0].strip()
            from_date = config_parts[1].strip()
            to_date = config_parts[2].strip()
            type_token = config_parts[3].strip()

            if action.get() == 5:
                export_refund_reward_to_excel(event, from_date, to_date, type_token)
            else:
                export_random_winners_to_excel(event, from_date, to_date, type_token)

        elif action.get() in [6, 7]:
            if len(config_parts) != 2:
                messagebox.showerror("Input Error", "Please provide user and community in the format 'user, community'.")
                return

            user = config_parts[0].strip()
            community = config_parts[1].strip()
            action_type = "add" if action.get() == 6 else "delete"
            edit_manager_to_community(user, community, action_type)

        elif action.get() == 8:
            if len(config_parts) != 2:
                messagebox.showerror("Input Error", "Please provide user and event in the format 'user, event'.")
                return

            user = config_parts[0].strip()
            event_id = config_parts[1].strip()
            check_point_user(user, event_id)

        else:
            event_configurations = []
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
            elif action.get() == 10:
                export_address_counts_to_excel(event_configurations)
            else:
                results.append("Invalid action")

        show_results()
        root.quit()

    submit_button = tk.Button(root, text="Submit", command=on_submit, bg="#4CAF50", fg="white", font=("Helvetica", 12), width=15)
    submit_button.pack(pady=10)

    root.mainloop()

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

ask_user_action()
