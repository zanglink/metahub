import requests
import json
import random
import math
import time
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
USER_DO_QUEST = f"{EVENT_URL}userDoQuest"
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
            # Chỉ thêm những user có 'ic' lớn hơn 0
            return [user['user']['address'] for user in data['data'] if user['user'].get('ic', 0) > 0]
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

def calculate_percentage(a, b):
    try:
        # Tính % của a trên b và làm tròn đến 2 chữ số thập phân
        percentage = round((a / b) * 100, 2)
        return percentage
    except (ZeroDivisionError, TypeError):
        # Nếu xảy ra lỗi chia cho 0 hoặc giá trị không hợp lệ, trả về 0
        return 0

def export_refund_reward_to_excel(from_date, to_date, max_page):
    max_page = int(max_page)  # Chuyển đổi max_page sang kiểu số nguyên
    all_rows = []

    for page in range(max_page + 1):
        params = {
            "from": format_date(from_date),
            "to": format_date(to_date),
            "page": page,
            "key": API_KEY
        }
        
        response = requests.get(REFUND_REWARD_URL, params=params)
        
        if response.status_code == 200:
            try:
                data = response.json().get('data', {}).get('data', [])
                if data:
                    for event_data in data:
                        token = event_data.get('token', '')
                        event_id = event_data.get('event', '')
                        event_counter = event_data.get('eventId', '')
                        event_title = event_data.get('title', '')
                        event_start = event_data.get('start', '')
                        event_end = event_data.get('end', '')
                        chain = event_data.get('chain', '')
                        total_fund_amount = event_data.get('totalFundTokenAmount', 0)
                        total_refund_amount = event_data.get('totalRefundAmount', 0)
                        total_user_reward = event_data.get('totalUserReward', 0)
                        total_bot_refund = event_data.get('totalBotRefund', 0)
                        percent = calculate_percentage(total_bot_refund, total_fund_amount)
                        
                        all_rows.append({
                            '#': len(all_rows) + 1,  # Số thứ tự tăng dần
                            'Event ID': event_id,
                            'ID': event_counter,
                            'Event Title': event_title,
                            'Start Day': event_start,
                            'End Day': event_end,
                            'Token': token,
                            'Chain': chain,
                            'Total Fund Token Amount': total_fund_amount,
                            'Total Refund Amount': total_refund_amount,
                            'Total User Reward': total_user_reward,
                            'Total Bot Refund': total_bot_refund,
                            'Percent': percent
                        })
                else:
                    results.append(f"No data found for page {page}.")
            except Exception as e:
                results.append(f"Error processing data for page {page}: {str(e)}")
        else:
            results.append(f"Failed to fetch data for page {page}. Status code: {response.status_code}")
            results.append(f"Error message: {response.text}")

    if all_rows:
        df = pd.DataFrame(all_rows)
        file_name = f"refund_reward_{from_date}_{to_date}_pages_0_to_{max_page}.xlsx"
        df.to_excel(file_name, index=False)
        results.append(f"Data has been saved to {file_name}")
    else:
        results.append("No data found for the entire range of pages.")


def export_winners_to_excel(from_date, to_date, max_page):
    max_page = int(max_page)  # Chuyển đổi max_page sang kiểu số nguyên
    all_rows = []

    for page in range(max_page + 1):
        params = {
            "from": format_date(from_date),
            "to": format_date(to_date),
            "page": page,
            "key": API_KEY
        }

        response = requests.get(REFUND_REWARD_URL, params=params)
        
        if response.status_code == 200:
            try:
                data = response.json().get('data', {}).get('data', [])
                if data:
                    for event_data in data:
                        event_id = event_data.get('event', '')
                        event_counter = event_data.get('eventId', '')
                        event_title = event_data.get('title', '')
                        event_start = event_data.get('start', '')
                        event_end = event_data.get('end', '')
                        token = event_data.get('token', '')
                        chain = event_data.get('chain', '')
                        total_fund = event_data.get('totalFundTokenAmount', 0)
                        top_bonus = event_data.get('topBonusAmount', [])
                        random_bonus = event_data.get('randomBonusAmount', 0)
                        
                        for index, user in enumerate(event_data.get('topWinnerUsers', [])):
                            all_rows.append({
                                '#': len(all_rows) + 1,
                                'Event ID': event_id,
                                'ID': event_counter,
                                'Event Title': event_title,
                                'Start Day': event_start,
                                'End Day': event_end,
                                'Token': token,
                                'Chain': chain,
                                'Total Fund': total_fund,
                                'Winner Address': user.get('address', ''),
                                'Bonus Amount': top_bonus[index] if index < len(top_bonus) else 0,
                                'Reward Type': 'Top'
                            })

                        for user in event_data.get('randomWinnerUsers', []):
                            all_rows.append({
                                '#': len(all_rows) + 1,
                                'Event ID': event_id,
                                'Event Title': event_title,
                                'Token': token,
                                'Chain': chain,
                                'Total Fund': total_fund,
                                'Winner Address': user.get('address', ''),
                                'Bonus Amount': random_bonus,
                                'Reward Type': 'Random'
                            })
                else:
                    results.append(f"No data found for page {page}.")
            except Exception as e:
                results.append(f"Error processing data for page {page}: {str(e)}")
        else:
            results.append(f"Failed to fetch data for page {page}. Status code: {response.status_code}")
            results.append(f"Error message: {response.text}")

    if all_rows:
        df = pd.DataFrame(all_rows)
        file_name = f"winners_{from_date}_{to_date}_pages_0_to_{max_page}.xlsx"
        df.to_excel(file_name, index=False)
        results.append(f"Data has been saved to {file_name}")
    else:
        results.append("No data found for the entire range of pages.")

        results.append("No data found for the given parameters.")

def export_address_counts_to_excel(event_configurations):
    event_ids = [event['event_id'] for event in event_configurations]
    data = []

    max_ic_address = None
    max_ic_value = 0

    for event_id in event_ids:
        response = requests.get(GET_USERS_URL, params={"key": API_KEY, "event": event_id})
        
        if response.status_code == 200:
            data_response = response.json()
            if data_response['success']:
                users = data_response['data']
                address_count = len([user['user']['address'] for user in users])
                ic_count = sum(1 for user in users if user['user'].get('ic', 0) > 0)
                
                for user in users:
                    ic_value = user['user'].get('ic', 0)
                    if ic_value > max_ic_value:
                        max_ic_value = ic_value
                        max_ic_address = user['user']['address']
                
                data.append({'#': len(data) + 1, 'event_id': event_id, 'count': address_count, 'ic_count': ic_count})
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

    if max_ic_address:
        results.append(f"The address with the highest IC is {max_ic_address} with IC value {max_ic_value}.")
    else:
        results.append("No address with IC value greater than 0 found.")

    for result in results:
        print(result)

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
            points_data = data.get('data', {})
            total_point = points_data.get('totalPoint', 'No total point available')
            point_from_event = points_data.get('pointFromEvent', 'No event point available')
            point_from_ref = points_data.get('pointFromRef', 'No referral point available')
            total_ref = points_data.get('totalRef', 'No total ref available')
            ref_histories = points_data.get('refHistories', [])

            # Show data into results
            results.append(f"User: {user}, Event: {event_id}")
            results.append(f"Total Points: {total_point}")
            results.append(f"Points from Event: {point_from_event}")
            results.append(f"Points from Referrals: {point_from_ref}")
            results.append(f"Total Referrals: {total_ref}")

            if ref_histories:
                results.append("Referral Histories:")
                for ref in ref_histories:
                    ref_user = ref.get('user', {})
                    ref_user_address = ref_user.get('address', 'No address available')
                    ref_user_username = ref_user.get('username', 'No username available')
                    inviter_id = ref.get('inviter', 'No inviter available')
                    ref_event_id = ref.get('event', 'No event available')

                    results.append(f"  - User Address: {ref_user_address}, Username: {ref_user_username}")
                    results.append(f"    Inviter ID: {inviter_id}, Event ID: {ref_event_id}")
            else:
                results.append("No referral histories available.")
        else:
            results.append(f"Failed to retrieve points. Response was unsuccessful. Data: {data}")
    else:
        results.append(f"Failed to retrieve points. Status code: {response.status_code}. Error message: {response.text}")


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
            5: "from, to",
            6: "user, community", 
            7: "user, community",
            8: "user, event_id",
            9: "from, to",
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
    # ttk.Radiobutton(excel_actions_frame, text="Check Point User", variable=action, value=8).pack(anchor=tk.W)
    ttk.Radiobutton(excel_actions_frame, text="Export Refund Reward to Excel", variable=action, value=5).pack(anchor=tk.W)
    ttk.Radiobutton(excel_actions_frame, text="Export Reward Winner to Excel", variable=action, value=9).pack(anchor=tk.W)
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
            if len(config_parts) != 3:
                messagebox.showerror("Input Error", "Please provide  from, to in the format 'from, to'.")
                return

            from_date = config_parts[0].strip()
            to_date = config_parts[1].strip()
            max_page = config_parts[2].strip()

            if action.get() == 5:
                export_refund_reward_to_excel(from_date, to_date, max_page)
            else:
                export_winners_to_excel(from_date, to_date, max_page)

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