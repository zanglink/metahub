# event_processor.py
import requests
import logging
from api_manager import (
    create_event, get_addresses, set_random_winners, stop_add_bot, add_random_bot, 
    check_point_user, list_user_is_bot, update_point_user,
    API_KEY, REFUND_REWARD_URL, USER_DO_QUEST_URL
)
from utils import calculate_percentage, format_date, select_random_addresses, filter_addresses, replace_addresses,  fetch_page_data, fetch_user_do_quest_page_data
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from itertools import chain  # Import chain
from collections import defaultdict  # Import defaultdict

logger = logging.getLogger(__name__)

def process_events(event_configurations):
    """Xử lý sự kiện: lấy địa chỉ người dùng, chọn ngẫu nhiên và đặt người thắng."""
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

def create_all_events(event_configurations):
    """Tạo tất cả các sự kiện."""
    for config in event_configurations:
        create_event(config["event_id"])

def stop_add_bot_all_events(event_configurations):
    """Dừng thêm bot cho tất cả các sự kiện."""
    for config in event_configurations:
        stop_add_bot(config["event_id"])

def add_random_bot_all_events(event_configurations):
    """Thêm bot ngẫu nhiên vào tất cả các sự kiện."""
    for config in event_configurations:
        add_random_bot(config["event_id"], config["count"])

def export_refund_reward_to_excel(from_date, to_date):
    """Xuất dữ liệu refund reward ra file Excel."""
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
            max_page = (count + 11) // 12  # Chia cho 12 và làm tròn lên để tính số trang

            with ThreadPoolExecutor(max_workers=10) as executor:  # Sử dụng tối đa 10 luồng song song
                # Truyền đúng đối số params vào fetch_page_data
                future_to_page = {
                    executor.submit(fetch_page_data, REFUND_REWARD_URL, {
                        "from": format_date(from_date),
                        "to": format_date(to_date),
                        "page": page,
                        "key": API_KEY
                    }): page for page in range(max_page)
                }

                for future in as_completed(future_to_page):
                    page_data = future.result()
                    for event_data in page_data:
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

                try:
                    with pd.ExcelWriter(file_name) as writer:
                        df_main.to_excel(writer, sheet_name='Refund Reward', index=False)
                        df_summary.to_excel(writer, sheet_name='Token Summary', index=False)
                    logger.info(f"Data has been saved to {file_name}")
                except Exception as e:
                    logger.error(f"Failed to save data to Excel: {str(e)}")
            else:
                logger.warning("No data found for the entire range of pages.")

        except Exception as e:
            logger.error(f"Error processing initial data: {str(e)}")
    else:
        logger.error(f"Failed to fetch initial data. Status code: {initial_response.status_code}")
        logger.error(f"Error message: {initial_response.text}")

def export_winners_to_excel(from_date, to_date):
    """Xuất danh sách người thắng ra file Excel."""
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

def export_user_do_quest_to_excel(event_configurations):
    """Xuất dữ liệu user do quest ra file Excel."""
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
            max_page = (count + 99) // 100  # Chia cho 100 và làm tròn lên để tính số trang
        else:
            logger.error(f"Failed to fetch initial data for event {event_id}. Status code: {response.status_code}")
            logger.error(f"Error message: {response.text}")
            continue

        real_user_count = 0
        user_ic_count = 0
        bot_count = 0
        logger.info(f"Loading data from event {event_id} with {max_page} pages")

        # Sử dụng ThreadPoolExecutor để xử lý song song
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_page = {
                executor.submit(fetch_user_do_quest_page_data, {**params, "page": page}): page for page in range(max_page)
            }

            for future in as_completed(future_to_page):
                page_data = future.result()

                for user_entry in page_data:
                    user_info = user_entry.get('user', {})
                    if user_info.get('isBot', False):
                        bot_count += 1
                    else:
                        real_user_count += 1
                        if user_info.get('ic', 0) > 0:
                            user_ic_count += 1

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
        try:
            df.to_excel(file_name, index=False)
            logger.info(f"Data has been saved to {file_name}")    
        except Exception as e:
            logger.error(f"Failed to save data to Excel: {str(e)}")
    else:
        logger.warning("No data found for the given events.")
