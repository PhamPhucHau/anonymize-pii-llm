from anonLLM.llm_ollama import OllamaLanguageModel   # Thay your_module bằng tên file bạn đã lưu
from pydantic import BaseModel

class OutputFormat(BaseModel):
    summary: str

prompt = "My name is Alice. I live in Paris and work at Google."

model = OllamaLanguageModel(anonymize=False)
result = model.generate(prompt, output_format=OutputFormat)
print("🏁 Kết quả cuối cùng:", result)
