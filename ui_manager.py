# ui_manager.py

import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.ttk import Progressbar
import logging
from event_processor import (
    process_events, create_all_events, stop_add_bot_all_events, 
    add_random_bot_all_events, export_refund_reward_to_excel, 
    export_winners_to_excel, export_user_do_quest_to_excel
)
from api_manager import edit_manager_to_community, check_point_user, update_point_user

logger = logging.getLogger(__name__)

def ask_user_action():
    """Hiển thị giao diện người dùng để chọn hành động."""
    root = tk.Tk()
    root.title("Choose Action")
    root.geometry("600x800")  # Đảm bảo cửa sổ đủ lớn để hiển thị tất cả các thành phần
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
        """Cập nhật gợi ý nhập liệu dựa trên hành động được chọn."""
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

    # Các tùy chọn hành động cho sự kiện
    ttk.Radiobutton(event_actions_frame, text="Create Bot On Top All Events", variable=action, value=1).pack(anchor=tk.W)
    ttk.Radiobutton(event_actions_frame, text="Stop Add Bot All Events", variable=action, value=2).pack(anchor=tk.W)
    ttk.Radiobutton(event_actions_frame, text="Random Winner All Events", variable=action, value=3).pack(anchor=tk.W)
    ttk.Radiobutton(event_actions_frame, text="Add Random Bot All Events", variable=action, value=4).pack(anchor=tk.W)
    ttk.Radiobutton(event_actions_frame, text="Update Point User", variable=action, value=12).pack(anchor=tk.W)

    # Các tùy chọn xuất dữ liệu ra Excel
    ttk.Radiobutton(excel_actions_frame, text="Check Point User", variable=action, value=8).pack(anchor=tk.W)
    ttk.Radiobutton(excel_actions_frame, text="Export Refund Reward to Excel", variable=action, value=5).pack(anchor=tk.W)
    ttk.Radiobutton(excel_actions_frame, text="Export Reward Winner to Excel", variable=action, value=9).pack(anchor=tk.W)
    ttk.Radiobutton(excel_actions_frame, text="Export User Do Quest to Excel", variable=action, value=11).pack(anchor=tk.W)

    # Các tùy chọn quản lý cộng đồng
    ttk.Radiobutton(community_actions_frame, text="Add manager to Community", variable=action, value=6).pack(anchor=tk.W)
    ttk.Radiobutton(community_actions_frame, text="Delete manager to Community", variable=action, value=7).pack(anchor=tk.W)

    config_label = tk.Label(root, text="Enter event configurations:", bg="#f0f0f0", font=("Helvetica", 14))
    config_label.pack(pady=10)

    config_input = tk.Text(root, height=5, width=40)
    config_input.pack(pady=10)

    # Tạo Progress Bar
    progress_bar = Progressbar(root, mode='indeterminate')

    def on_submit():
        """Xử lý hành động khi người dùng nhấn nút Submit."""
        progress_bar.pack(pady=10)
        progress_bar.start()

        config_data = config_input.get("1.0", tk.END).strip()
        global event_configurations
        event_configurations = []
        config_parts = config_data.split(',')

        # Xác nhận trước khi thực hiện hành động quan trọng
        if action.get() in [6, 7, 12]:
            confirmation = messagebox.askyesno("Confirmation", "Are you sure you want to proceed with this action?")
            if not confirmation:
                progress_bar.stop()
                progress_bar.pack_forget()
                return

        # Xử lý các hành động dựa trên tùy chọn được chọn
        try:
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

        except Exception as e:
            logger.error(f"An error occurred: {e}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            progress_bar.stop()
            progress_bar.pack_forget()
            show_results()
            root.quit()

    submit_button = tk.Button(root, text="Submit", command=on_submit, bg="#4CAF50", fg="white", font=("Helvetica", 12), width=15)
    submit_button.pack(pady=10)  # Sử dụng pack() để đảm bảo nút Submit hiển thị

    root.mainloop()

def show_results():
    """Hiển thị kết quả từ file log trong giao diện."""
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
    try:
        with open("app.log", "r") as log_file:
            for line in log_file:
                # Mỗi dòng log có định dạng: Timestamp - Logger - Level - Message
                parts = line.split(" - ", 3)  # Chia thành 4 phần: Timestamp, Logger, Level và Message
                if len(parts) == 4:
                    tree.insert("", tk.END, values=parts)
    except FileNotFoundError:
        logger.error("Log file not found.")
        messagebox.showerror("File Error", "Log file not found.")

    # Tạo Frame chứa nút "Close"
    button_frame = tk.Frame(result_window, bg="#f0f0f0")
    button_frame.pack(side=tk.BOTTOM, pady=10, fill=tk.X)

    close_button = tk.Button(button_frame, text="Close", command=result_window.destroy, bg="#4CAF50", fg="white", font=("Helvetica", 12), width=15)
    close_button.pack(pady=10)

    result_window.mainloop()
