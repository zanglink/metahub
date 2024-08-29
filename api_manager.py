# api_manager.py

import requests
import logging
import random

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

def stop_add_bot(event_id):
    payload = {"event": event_id, "status": True}
    response = requests.patch(STOP_ADD_BOT_URL, json=payload, params={"key": API_KEY}, headers={"Content-Type": "application/json"})
    
    if response.status_code == 200:
        logger.info(f"Successfully stopped adding bot for event {event_id}.")
    else:
        logger.error(f"Failed to stop adding bot for event {event_id}. Status code: {response.status_code}")
        logger.error(f"Error message: {response.text}")

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

            return ref_histories
        else:
            logger.error(f"Failed to retrieve points. Response was unsuccessful. Data: {data}")
            return []
    else:
        logger.error(f"Failed to retrieve points. Status code: {response.status_code}. Error message: {response.text}")
        return []

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
