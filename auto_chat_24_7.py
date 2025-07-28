import time
import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os
from anonLLM.llm_ollama import OllamaLanguageModel

# Load môi trường
load_dotenv()
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
FORWARD_TO = os.getenv("FORWARD_TO")

# Khởi tạo LLM
llm = OllamaLanguageModel(
    model="mistral:latest",         # hoặc "mixtral", "llama3", tùy theo model bạn đã tải với ollama
    temperature=0.7,
    anonymize=True           # nếu muốn ẩn danh dữ liệu cá nhân
)

def fetch_unseen_emails():
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(EMAIL, PASSWORD)
    mail.select("inbox")

    status, messages = mail.search(None, '(UNSEEN)')
    email_ids = messages[0].split()

    emails = []
    for eid in email_ids:
        status, data = mail.fetch(eid, "(RFC822)")
        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)
        subject = msg["Subject"]
        from_addr = msg["From"]

        # Lấy nội dung text với xử lý charset
        body = None
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    charset = part.get_content_charset() or "utf-8"
                    try:
                        body = part.get_payload(decode=True).decode(charset)
                    except (UnicodeDecodeError, LookupError):
                        # Fallback decode latin1 nếu lỗi
                        body = part.get_payload(decode=True).decode("latin1", errors="ignore")
                    break
        else:
            charset = msg.get_content_charset() or "utf-8"
            try:
                body = msg.get_payload(decode=True).decode(charset)
            except (UnicodeDecodeError, LookupError):
                body = msg.get_payload(decode=True).decode("latin1", errors="ignore")

        emails.append((eid, from_addr, subject, body))
    mail.logout()
    return emails

def send_email(to_addr, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL
    msg["To"] = to_addr

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL, PASSWORD)
        server.sendmail(EMAIL, to_addr, msg.as_string())

def auto_process():
    emails = fetch_unseen_emails()
    if not emails:
        print("📭 Không có email mới.")
        return

    for eid, sender, subject, body in emails:
        print(f"\n📨 Email mới từ {sender} - Chủ đề: {subject}")
        print("🔍 Đang xử lý nội dung...")

        prompt = f"Trả lời lịch sự và ngắn gọn email sau và ẩn danh thông tin cá nhân:\n\n{body}"
        reply_text = llm.generate(prompt)

        print("✅ Nội dung phản hồi đã được sinh ra.")
        return
        # Gửi lại cho người gửi
        send_email(sender, f"Re: {subject}", reply_text)
        print(f"✉️ Đã auto reply cho {sender}")

        # Forward email đã ẩn danh cho coworker
        forward_text = f"Email từ {sender} với nội dung đã được xử lý:\n\n{reply_text}"
        send_email(FORWARD_TO, f"FWD: {subject}", forward_text)
        print(f"📤 Đã forward cho {FORWARD_TO}")

if __name__ == "__main__":
    print("🚀 Dịch vụ kiểm tra email đang chạy... (Ctrl+C để dừng)")
    while True:
        try:
            auto_process()
        except Exception as e:
            print(f"❌ Lỗi: {e}")
        time.sleep(60)  # Kiểm tra mỗi 60 giây
