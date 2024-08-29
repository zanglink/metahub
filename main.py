# main.py

import logging
from ui_manager import ask_user_action

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """
    Hàm main khởi động ứng dụng.
    """
    logger.info("Application started.")
    
    try:
        # Gọi hàm hiển thị giao diện người dùng từ ui_manager
        ask_user_action()
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise
    finally:
        logger.info("Application ended.")

if __name__ == "__main__":
    main()
