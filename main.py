import requests
import logging
from itertools import chain
import random
import math
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from datetime import datetime
from collections import defaultdict

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

# Tạo logger
logger = logging.getLogger(__name__)

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
USER_DO_QUEST_URL = f"{EVENT_URL}userDoQuest"
REFUND_REWARD_URL = f"{BASE_URL}refundReward"
EDIT_USER_COMMUNITY_URL = f"{COMMUNITY_URL}private/manager"
CHECK_POINT = f"{EVENT_URL}private/userPoint"
UPDATE_POINT = f"{EVENT_URL}userPoint"

def create_event(event_id):
    payload = {"event": event_id}
    response = requests.post(CREATE_URL, json=payload, params={"key": API_KEY}, headers={"Content-Type": "application/json"})
    
    if response.status_code == 200:
        logger.info(f"Event {event_id} created successfully.")
        return response.json()
    else:
        logger.error(f"Failed to create event {event_id}. Status code: {response.status_code}")
        logger.error(f"Error message: {response.text}")
        return None

def get_addresses(event_id):
    response = requests.get(GET_USERS_URL, params={"key": API_KEY, "event": event_id})
    
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            return [user['user']['address'] for user in data['data'] if user['user'].get('ic', 0) > 0]
        else:
            logger.error(f"API response unsuccessful for event {event_id}.")
            return []
    else:
        logger.error(f"Failed to fetch data for event {event_id}. Status code: {response.status_code}")
        logger.error(f"Error message: {response.text}")
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
            logger.info(f"Successfully set random winners for event {event_id}.")
        else:
            logger.error(f"Failed to set random winners for event {event_id}. Response was unsuccessful.")
            logger.error(f"Error message: {data}")
    else:
        logger.error(f"Failed to set random winners for event {event_id}. Status code: {response.status_code}")
        logger.error(f"Error message: {response.text}")

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
            logger.info(f"Selected addresses for event {event_id}: {selected_addresses}")
            set_random_winners(event_id, selected_addresses)
        else:
            logger.warning(f"No addresses found for event {event_id}")

def stop_add_bot(event_id):
    payload = {"event": event_id, "status": True}
    response = requests.patch(STOP_ADD_BOT_URL, json=payload, params={"key": API_KEY}, headers={"Content-Type": "application/json"})
    
    if response.status_code == 200:
        logger.info(f"Successfully stopped adding bot for event {event_id}.")
    else:
        logger.error(f"Failed to stop adding bot for event {event_id}. Status code: {response.status_code}")
        logger.error(f"Error message: {response.text}")

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
            logger.info(f"Successfully added {current_chunk_size} random bots for event {event_id}.")
        else:
            logger.error(f"Failed to add {current_chunk_size} random bots for event {event_id}. Status code: {response.status_code}")
            logger.error(f"Error message: {response.text}")
        
        count -= current_chunk_size

def add_random_bot_all_events(event_configurations):
    for config in event_configurations:
        add_random_bot(config["event_id"], config["count"])

def format_date(date_str):
    return datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y-%m-%dT00:00:00.000Z')

def calculate_percentage(a, b):
    try:
        percentage = round((a / b) * 100, 2)
        return percentage
    except (ZeroDivisionError, TypeError):
        return 0

def export_refund_reward_to_excel(from_date, to_date):
    all_rows = []
    token_summary = defaultdict(lambda: {
        'Chain': '',
        'Total Fund Token Amount': 0,
        'Total Refund Amount': 0,
        'Total User Reward': 0,
        'Total Bot Refund': 0
    })

    initial_params = {
        "from": format_date(from_date),
        "to": format_date(to_date),
        "page": 0,
        "key": API_KEY
    }
    
    initial_response = requests.get(REFUND_REWARD_URL, params=initial_params)
    
    if initial_response.status_code == 200:
        try:
            initial_data = initial_response.json().get('data', {})
            count = initial_data.get('count', 0)
            max_page = math.floor(count / 12)
            
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
                                all_rows.append({
                                    'ID': event_data.get('eventId', ''),
                                    'Event ID': event_data.get('event', ''),
                                    'Event Title': event_data.get('title', ''),
                                    'Start Day': event_data.get('start', ''),
                                    'End Day': event_data.get('end', ''),
                                    'Token': event_data.get('token', ''),
                                    'Chain': event_data.get('chain', ''),
                                    'Total Fund Token Amount': event_data.get('totalFundTokenAmount', 0),
                                    'Total Refund Amount': event_data.get('totalRefundAmount', 0),
                                    'Total User Reward': event_data.get('totalUserReward', 0),
                                    'Total Bot Refund': event_data.get('totalBotRefund', 0),
                                    'Percent': calculate_percentage(
                                        event_data.get('totalBotRefund', 0),
                                        event_data.get('totalFundTokenAmount', 0)
                                    )
                                })
                                
                                token = event_data.get('token', '')
                                token_summary[token]['Chain'] = event_data.get('chain', '')
                                token_summary[token]['Total Fund Token Amount'] += event_data.get('totalFundTokenAmount', 0)
                                token_summary[token]['Total Refund Amount'] += event_data.get('totalRefundAmount', 0)
                                token_summary[token]['Total User Reward'] += event_data.get('totalUserReward', 0)
                                token_summary[token]['Total Bot Refund'] += event_data.get('totalBotRefund', 0)
                        else:
                            logger.warning(f"No data found for page {page}.")
                    except Exception as e:
                        logger.error(f"Error processing data for page {page}: {str(e)}")
                else:
                    logger.error(f"Failed to fetch data for page {page}. Status code: {response.status_code}")
                    logger.error(f"Error message: {response.text}")
        
            if all_rows:
                all_rows = sorted(all_rows, key=lambda x: x['ID'])

                df_main = pd.DataFrame(all_rows)
                file_name = f"refund_reward_{from_date}_{to_date}_pages_0_to_{max_page}.xlsx"
                
                token_summary_rows = [
                    {
                        '#': i + 1,
                        'Token': token,
                        'Chain': data['Chain'],
                        'Total Fund Token Amount': data['Total Fund Token Amount'],
                        'Total Refund Amount': data['Total Refund Amount'],
                        'Total User Reward': data['Total User Reward'],
                        'Total Bot Refund': data['Total Bot Refund']
                    }
                    for i, (token, data) in enumerate(token_summary.items())
                ]
                df_summary = pd.DataFrame(token_summary_rows)

                with pd.ExcelWriter(file_name) as writer:
                    df_main.to_excel(writer, sheet_name='Refund Reward', index=False)
                    df_summary.to_excel(writer, sheet_name='Token Summary', index=False)
                
                logger.info(f"Data has been saved to {file_name}")
            else:
                logger.warning("No data found for the entire range of pages.")
                
        except Exception as e:
            logger.error(f"Error processing initial data: {str(e)}")
    else:
        logger.error(f"Failed to fetch initial data. Status code: {initial_response.status_code}")
        logger.error(f"Error message: {initial_response.text}")

def export_winners_to_excel(from_date, to_date):
    all_rows = []
    wallet_data = {}

    page = 0
    while True:
        params = {
            "from": format_date(from_date),
            "to": format_date(to_date),
            "page": page,
            "key": API_KEY
        }

        response = requests.get(REFUND_REWARD_URL, params=params)

        if response.status_code == 200:
            try:
                data = response.json().get('data', {})
                count = data.get('count', 0)
                page_data = data.get('data', [])

                if page_data:
                    for event_data in page_data:
                        for index, user in enumerate(chain(
                                event_data.get('topWinnerUsers', []), 
                                event_data.get('randomWinnerUsers', []))):
                            
                            if user.get('isBot', False):
                                continue
                            
                            token = event_data.get('token', '')
                            wallet = user.get('address', '')
                            bonus_amount = (event_data.get('topBonusAmount', [])[index] 
                                            if index < len(event_data.get('topBonusAmount', []))
                                            else event_data.get('randomBonusAmount', 0))

                            all_rows.append({
                                'ID': event_data.get('eventId', ''),
                                'Event ID': event_data.get('event', ''),
                                'Event Title': event_data.get('title', ''),
                                'Token': token,
                                'Chain': event_data.get('chain', ''),
                                'Winner Address': wallet,
                                'Bonus Amount': bonus_amount,
                                'Reward Type': 'Top' if index < len(event_data.get('topBonusAmount', [])) else 'Random'
                            })

                            if (wallet, token) in wallet_data:
                                wallet_data[(wallet, token)] += bonus_amount
                            else:
                                wallet_data[(wallet, token)] = bonus_amount

                max_page = (count + len(page_data) - 1) // len(page_data)
                if page >= max_page:
                    break

                page += 1

            except Exception as e:
                logger.error(f"Error processing data for page {page}: {str(e)}")
                break
        else:
            logger.error(f"Failed to fetch data for page {page}. Status code: {response.status_code}")
            logger.error(f"Error message: {response.text}")
            break

    if all_rows:
        all_rows = sorted(all_rows, key=lambda x: x['ID'])
        df_main = pd.DataFrame(all_rows)
        file_name = f"winners_{from_date}_{to_date}.xlsx"
        
        wallet_summary = [{'#': i+1, 'Wallet': wallet, 'Amount': amount, 'Token': token}
                          for i, ((wallet, token), amount) in enumerate(wallet_data.items())]
        df_summary = pd.DataFrame(wallet_summary).sort_values(by=['Token', 'Amount'], ascending=[True, False])

        with pd.ExcelWriter(file_name) as writer:
            df_main.to_excel(writer, sheet_name='Winners', index=False)
            df_summary.to_excel(writer, sheet_name='Wallet Summary', index=False)
        
        logger.info(f"Data has been saved to {file_name}")
    else:
        logger.warning("No data found for the entire range of pages.")

def export_user_do_quest_to_excel(event_configurations):
    all_rows = []

    for event_config in event_configurations:
        event_id = event_config.get("event_id", "")
        params = {
            "key": API_KEY,
            "event": event_id
        }

        response = requests.get(USER_DO_QUEST_URL, params=params)
        if response.status_code == 200:
            data = response.json().get('data', {})
            count = data.get('count', 0)
            max_page = (count // 100) + (1 if count % 100 > 0 else 0)
        else:
            logger.error(f"Failed to fetch initial data for event {event_id}. Status code: {response.status_code}")
            logger.error(f"Error message: {response.text}")
            continue

        real_user_count = 0
        user_ic_count = 0
        bot_count = 0
        logger.info(f"Loading data from event {event_id} with {max_page} pages")

        for page in range(max_page):
            params.update({"page": page})
            response = requests.get(USER_DO_QUEST_URL, params=params)
            logger.info(f"Processing data page {page}")
            if response.status_code == 200:
                try:
                    data = response.json().get('data', {})
                    user_data = data.get('data', [])
                    
                    for user_entry in user_data:
                        user_info = user_entry.get('user', {})
                        if user_info.get('isBot', False):
                            bot_count += 1
                        else:
                            real_user_count += 1
                            if user_info.get('ic', 0) > 0:
                                user_ic_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing data for event {event_id}, page {page}: {str(e)}")
            else:
                logger.error(f"Failed to fetch data for event {event_id}, page {page}. Status code: {response.status_code}")
                logger.error(f"Error message: {response.text}")

        rate_user = real_user_count / (real_user_count + bot_count) if (real_user_count + bot_count) > 0 else 0
        
        all_rows.append({
            'Event ID': event_id,
            'Total User': real_user_count + bot_count,
            'Real User': real_user_count,
            'User IC': user_ic_count,
            'Bot': bot_count,
            'Rate User': rate_user
        })

    if all_rows:
        df = pd.DataFrame(all_rows)
        file_name = f"user_do_quest_{event_id}.xlsx"
        df.to_excel(file_name, index=False)
        logger.info(f"Data has been saved to {file_name}")    
    else:
        logger.warning("No data found for the given events.")

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
            logger.info(f"Successfully edited manager {user} to community {community}.")
        else:
            logger.error(f"Failed to edit manager {user} to community {community}. Response was unsuccessful.")
            logger.error(f"Error message: {data}")
    else:
        logger.error(f"Failed to edit manager {user} to community {community}. Status code: {response.status_code}")
        logger.error(f"Error message: {response.text}")


def check_time_do_quest(event_id, list_address):
    params = {
        "key": API_KEY,
        "event": event_id
    }

    # Tính toán số trang tối đa (max_page) bằng cách lấy count từ trang đầu tiên
    response = requests.get(USER_DO_QUEST_URL, params=params)
    if response.status_code == 200:
        try:
            data = response.json().get('data', {})
            count = data.get('count', 0)
            max_page = (count // 100) + (1 if count % 100 > 0 else 0)
        except ValueError as e:
            logger.error(f"Error decoding JSON response: {e}")
            return
    else:
        logger.error(f"Failed to fetch initial data for event {event_id}. Status code: {response.status_code}")
        logger.error(f"Error message: {response.text}")
        return

    logger.info(f"Loading data from event {event_id} with {max_page} pages")

    # Gọi API theo từng trang và kiểm tra địa chỉ
    for page in range(max_page):
        params.update({"page": page})
        response = requests.get(USER_DO_QUEST_URL, params=params)
        logger.info(f"Processing data page {page}")
        if response.status_code == 200:
            try:
                page_data = response.json().get('data', {}).get('data', [])

                if not isinstance(page_data, list):
                    logger.error(f"Unexpected data format: {page_data}")
                    continue

                for entry in page_data:
                    user_info = entry.get('user', {})
                    address = user_info.get('address', '')
                    ic = user_info.get('ic', '')
                    created_at = entry.get('createdAt', '')

                    if address in list_address:
                        logger.info(f"Address: {address} \nCreated At: {created_at} \nIC: {ic}")

            except ValueError as e:
                logger.error(f"Error decoding JSON response: {e}")
            except Exception as e:
                logger.error(f"Error processing data for event {event_id}, page {page}: {str(e)}")
        else:
            logger.error(f"Failed to fetch data for event {event_id}, page {page}. Status code: {response.status_code}")
            logger.error(f"Error message: {response.text}")

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

            logger.info(f"User: {user}, Event: {event_id}")
            logger.info(f"Total Points: {total_point}")
            logger.info(f"Points from Event: {point_from_event}")
            logger.info(f"Points from Referrals: {point_from_ref}")
            logger.info(f"Total Referrals: {total_ref}")

            list_address = [ref.get('user', {}).get('address', 'No address available') for ref in ref_histories]
            check_time_do_quest(event_id, list_address)
            
        else:
            logger.error(f"Failed to retrieve points. Response was unsuccessful. Data: {data}")
    else:
        logger.error(f"Failed to retrieve points. Status code: {response.status_code}. Error message: {response.text}")

def list_user_is_bot(event_id, amount):
    user_is_bot = []
    page = 0

    while len(user_is_bot) < amount:
        params = {
            "key": API_KEY,
            "event": event_id,
            "page": page
        }
        
        response = requests.get(USER_DO_QUEST_URL, params=params)
        
        if response.status_code == 200:
            try:
                data = response.json().get('data', {})
                users = data.get('data', [])
                
                for user_entry in users:
                    user_info = user_entry.get('user', {})
                    if user_info.get('isBot', False):
                        user_is_bot.append(user_info.get('address', ''))

                    if len(user_is_bot) >= amount:
                        break

            except Exception as e:
                logger.error(f"Error processing data for page {page}: {str(e)}")
                break

        else:
            logger.error(f"Failed to fetch data for page {page}. Status code: {response.status_code}")
            logger.error(f"Error message: {response.text}")
            break

        page += 1
    return user_is_bot

def update_point_user(event_id, amount, min_value, max_value):
    list_wallet = list_user_is_bot(event_id, amount)
    
    if not list_wallet:
        logger.warning("No bot users found to update points.")
        return
    
    for wallet in list_wallet:
        number = random.randrange(min_value, max_value + 1, 10)
        payload = {
            "event": event_id,
            "user": wallet,
            "point": number
        }
        
        response = requests.post(UPDATE_POINT, json=payload, params={"key": API_KEY}, headers={"Content-Type": "application/json"})
        
        if response.status_code == 200:
            logger.info(f"Successfully updated {number} points for wallet {wallet}.")
        else:
            logger.error(f"Failed to update points for wallet {wallet}. Status code: {response.status_code}")
            logger.error(f"Error message: {response.text}")

def ask_user_action():
    root = tk.Tk()
    root.title("Choose Action")
    root.geometry("600x800")
    root.configure(bg="#f0f0f0")
    root.resizable(False, False)

    action = tk.IntVar()

    label = tk.Label(root, text="Choose action:", bg="#f0f0f0", font=("Helvetica", 14))
    label.pack(pady=10)

    style = ttk.Style()
    style.configure("TRadiobutton", background="#f0f0f0", font=("Helvetica", 12))

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
            10: "event_id",
            11: "event_id",
            12: "event_id, amount, min, max"
        }.get(action.get(), "")
        config_input.delete("1.0", tk.END)
        config_input.insert("1.0", placeholder_text)

    action.trace("w", update_placeholder)

    ttk.Radiobutton(event_actions_frame, text="Create Bot On Top All Events", variable=action, value=1).pack(anchor=tk.W)
    ttk.Radiobutton(event_actions_frame, text="Stop Add Bot All Events", variable=action, value=2).pack(anchor=tk.W)
    ttk.Radiobutton(event_actions_frame, text="Random Winner All Events", variable=action, value=3).pack(anchor=tk.W)
    ttk.Radiobutton(event_actions_frame, text="Add Random Bot All Events", variable=action, value=4).pack(anchor=tk.W)
    ttk.Radiobutton(event_actions_frame, text="Update Point User", variable=action, value=12).pack(anchor=tk.W)

    ttk.Radiobutton(excel_actions_frame, text="Check Point User", variable=action, value=8).pack(anchor=tk.W)
    ttk.Radiobutton(excel_actions_frame, text="Export Refund Reward to Excel", variable=action, value=5).pack(anchor=tk.W)
    ttk.Radiobutton(excel_actions_frame, text="Export Reward Winner to Excel", variable=action, value=9).pack(anchor=tk.W)
    ttk.Radiobutton(excel_actions_frame, text="Export User Do Quest to Excel", variable=action, value=11).pack(anchor=tk.W)

    ttk.Radiobutton(community_actions_frame, text="Add manager to Community", variable=action, value=6).pack(anchor=tk.W)
    ttk.Radiobutton(community_actions_frame, text="Delete manager to Community", variable=action, value=7).pack(anchor=tk.W)

    config_label = tk.Label(root, text="Enter event configurations:", bg="#f0f0f0", font=("Helvetica", 14))
    config_label.pack(pady=10)

    config_input = tk.Text(root, height=5, width=40)
    config_input.pack(pady=10)

    def on_submit():
        config_data = config_input.get("1.0", tk.END).strip()
        global event_configurations
        event_configurations = []
        
        config_parts = config_data.split(',')

        if action.get() in [5, 9]:
            if len(config_parts) != 2:
                messagebox.showerror("Input Error", "Please provide from, to in the format 'from, to'.")
                return

            from_date = config_parts[0].strip()
            to_date = config_parts[1].strip()

            if action.get() == 5:
                export_refund_reward_to_excel(from_date, to_date)
            else:
                export_winners_to_excel(from_date, to_date)

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

        elif action.get() == 12:
            if len(config_parts) != 4:
                messagebox.showerror("Input Error", "Please provide event_id, amount, min, max in the format 'event_id, amount, min, max'.")
                return

            event_id = config_parts[0].strip()
            amount = int(config_parts[1].strip())
            min_value = int(config_parts[2].strip())
            max_value = int(config_parts[3].strip())
            update_point_user(event_id, amount, min_value, max_value)

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
            elif action.get() == 11:
                export_user_do_quest_to_excel(event_configurations)
            else:
                logger.error("Invalid action")

        show_results()
        root.quit()

    submit_button = tk.Button(root, text="Submit", command=on_submit, bg="#4CAF50", fg="white", font=("Helvetica", 12), width=15)
    submit_button.pack(pady=10)

    root.mainloop()

def show_results():
    result_window = tk.Tk()
    result_window.title("Results")
    result_window.geometry("800x400")
    result_window.configure(bg="#f0f0f0")
    result_window.resizable(False, False)

    # Tạo Treeview để hiển thị kết quả dưới dạng bảng
    tree = ttk.Treeview(result_window, columns=("Timestamp", "Logger", "Level", "Message"), show='headings')
    tree.heading("Timestamp", text="Timestamp")
    tree.heading("Logger", text="Logger")
    tree.heading("Level", text="Level")
    tree.heading("Message", text="Message")

    # Đặt kích thước cột
    tree.column("Timestamp", width=150)
    tree.column("Logger", width=100)
    tree.column("Level", width=80)
    tree.column("Message", width=450)

    # Đặt Treeview vào cửa sổ
    tree.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

    # Đọc nội dung từ file log và hiển thị trong bảng
    with open("app.log", "r") as log_file:
        for line in log_file:
            # Mỗi dòng log có định dạng: Timestamp - Logger - Level - Message
            parts = line.split(" - ", 3)  # Chia thành 4 phần: Timestamp, Logger, Level và Message
            if len(parts) == 4:
                tree.insert("", tk.END, values=parts)

    # Tạo Frame chứa nút "Close"
    button_frame = tk.Frame(result_window, bg="#f0f0f0")
    button_frame.pack(side=tk.BOTTOM, pady=10, fill=tk.X)

    close_button = tk.Button(button_frame, text="Close", command=result_window.destroy, bg="#4CAF50", fg="white", font=("Helvetica", 12), width=15)
    close_button.pack(pady=10)

    result_window.mainloop()

ask_user_action()
