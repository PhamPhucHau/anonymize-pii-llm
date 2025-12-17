import os
from datetime import datetime

class AutoPrint:
    def __init__(self, log_file="autoprint.log", encoding="utf-8", timestamp=False):
        self.log_file = log_file
        self.encoding = encoding
        self.timestamp = timestamp

        # Tạo file mới hoặc ghi tiếp
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w", encoding=self.encoding) as f:
                f.write("🔸 AutoPrint log started\n")

    def print(self, message: str):
        if self.timestamp:
            now = datetime.now().strftime("[%Y-%m-%d %H:%M:%S] ")
            full_message = now + message
        else:
            full_message = message

        print(full_message)

        with open(self.log_file, "a", encoding=self.encoding) as f:
            f.write(full_message + "\n")
