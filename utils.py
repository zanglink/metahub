# utils.py

from datetime import datetime
import logging
import requests
from api_manager import (
    USER_DO_QUEST_URL
)

logger = logging.getLogger(__name__)

def format_date(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y-%m-%dT00:00:00.000Z')
    except ValueError as e:
        logger.error(f"Error formatting date {date_str}: {e}")
        return None

def calculate_percentage(a, b):
    try:
        if b == 0:
            return 0
        return round((a / b) * 100, 2)
    except (ZeroDivisionError, TypeError) as e:
        logger.error(f"Error calculating percentage: {e}")
        return 0

def select_random_addresses(addresses, count):
    import random
    if len(addresses) >= count:
        return random.sample(addresses, count)
    return addresses

def replace_addresses(address_a, address_b):
    import random
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

def fetch_page_data(url, params):
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json().get('data', {}).get('data', [])
        else:
            logger.error(f"Failed to fetch data for page {params.get('page')}. Status code: {response.status_code}")
            logger.error(f"Error message: {response.text}")
            return []
    except Exception as e:
        logger.error(f"Exception occurred while fetching data for page {params.get('page')}: {str(e)}")
        return []

def fetch_user_do_quest_page_data(params):
    try:
        response = requests.get(USER_DO_QUEST_URL, params=params)
        if response.status_code == 200:
            return response.json().get('data', {}).get('data', [])
        else:
            logger.error(f"Failed to fetch data for page {params.get('page')}. Status code: {response.status_code}")
            logger.error(f"Error message: {response.text}")
            return []
    except Exception as e:
        logger.error(f"Exception occurred while fetching user do quest data for page {params.get('page')}: {str(e)}")
        return []
