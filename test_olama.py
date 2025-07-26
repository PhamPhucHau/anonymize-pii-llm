from dotenv import load_dotenv
from anonLLM.llm_ollama import OllamaLanguageModel  # bạn đổi tên file gốc thành llm_ollama.py nếu cần

load_dotenv()

# Câu lệnh đầu vào
text = (
    "Write a CV for me: My name is Alice Johnson, "
    "email: alice.johnson@example.com, phone: +1 234-567-8910. "
    "I am a machine learning engineer."
)

# Khởi tạo mô hình Ollama
llm = OllamaLanguageModel(
    model="mistral:latest",         # hoặc "mixtral", "llama3", tùy theo model bạn đã tải với ollama
    temperature=0.7,
    anonymize=True           # nếu muốn ẩn danh dữ liệu cá nhân
)

# Gọi API để sinh văn bản
response = llm.generate(text,output_format=None)

# In kết quả
print("\n📝 Response:\n")
print(response)
