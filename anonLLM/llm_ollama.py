import time
import json
import requests
from pydantic import BaseModel, ValidationError, ConfigDict
from typing import Type, Optional
import os
from anonLLM.anonymizer import Anonymizer
from anonLLM.deanonymizer import Deanonymizer
from autoprint import AutoPrint

class OllamaLanguageModel:
    def __init__(self, model="mistral", temperature=0.5, anonymize=True, base_url="http://localhost:11434"):
        self.anonymize = anonymize
        self.base_url = base_url
        self.model = model
        self.temperature = temperature

        if self.anonymize:
            self.anonymizer = Anonymizer()
            self.deanonymizer = Deanonymizer()

    def generate(self, prompt: str, output_format: Optional[Type[BaseModel]] = None,
                 n_completions: int = 1, max_tokens: int = None):

        print("\n📌 Bắt đầu generate()")
        print(f"🔸 Prompt gốc: {prompt}")
        logger_before = AutoPrint(log_file="log/Before.txt", timestamp=True)
        logger_after = AutoPrint(log_file="log/After.txt", timestamp=True)
        logger_map = AutoPrint(log_file="log/Map.txt", timestamp=True)
        logger_before.print(f"🔸 Prompt gốc: {prompt}")
        if self.anonymize:
            print("🔐 Đang thực hiện ẩn danh hóa dữ liệu...")
            anonymized_prompt, mappings = self.anonymizer.anonymize_data(prompt)
            print(f"✅ Prompt sau khi ẩn danh: {anonymized_prompt}")
            logger_after.print(f"✅ Prompt sau khi ẩn danh: {anonymized_prompt}")
            print(f"📄 Mappings: {mappings}")
            logger_map.print(f"📄 Mappings: {mappings}")
        else:
            anonymized_prompt, mappings = prompt, None
            print("⚠️ Không thực hiện ẩn danh hóa.")

        valid_responses = []

        while len(valid_responses) < n_completions:
            try:
                print("\n🚀 Gửi yêu cầu tới mô hình Ollama...")

                system_message = "You are a helpful assistant."
                if output_format:
                    system_message += f" Respond in a JSON format that contains the following keys: {self._model_structure_repr(output_format)}"

                full_prompt = f"{system_message}\n{anonymized_prompt}"
                print(f"📤 Full prompt gửi đi:\n{full_prompt}")

                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": full_prompt,
                        "temperature": self.temperature
                    },
                    stream=True  # Quan trọng: enable streaming để nhận từng dòng JSON
                )

                print(f"📥 Phản hồi nhận được: {response.status_code}")
                if response.status_code != 200:
                    raise RuntimeError(f"❌ Lỗi từ Ollama: {response.text}")

                # Nối từng dòng JSON thành chuỗi text hoàn chỉnh
                text = ""
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line.decode("utf-8"))
                            text += data.get("response", "")
                        except json.JSONDecodeError as e:
                            print(f"❌ Lỗi khi decode JSON dòng: {line}\n{e}")

                print(f"🧾 Văn bản phản hồi tổng hợp:\n{text}")

                if output_format:
                    try:
                        parsed = json.loads(text)
                        print("🔍 Đang kiểm tra JSON có hợp lệ theo định dạng yêu cầu không...")
                        if self._is_valid_json_for_model(text, output_format):
                            print("✅ JSON hợp lệ.")
                            valid_responses.append(parsed)
                        else:
                            print("❌ JSON không hợp lệ.")
                    except json.JSONDecodeError as e:
                        print(f"❌ Lỗi khi parse JSON: {e}")
                else:
                    print("📄 Không yêu cầu định dạng JSON => thêm phản hồi raw.")
                    valid_responses.append(text)

            except Exception as err:
                print(f"❗ Exception xảy ra: {err}")
                break

        def _deanonymize(response):
            print(f"🔓 Gỡ ẩn danh phản hồi: {response}")
            if output_format:
                for key, value in response.items():
                    response[key] = self.deanonymizer.deanonymize(value, mappings)
                return output_format.model_validate(response)
            else:
                return self.deanonymizer.deanonymize(response, mappings)

        if not valid_responses:
            raise ValueError("❌ Không có phản hồi hợp lệ từ mô hình.")

        deanonymized_responses = [_deanonymize(res) if self.anonymize else res
                                  for res in valid_responses]

        result = deanonymized_responses[0] if n_completions == 1 else deanonymized_responses
        print(f"\n✅ Phản hồi cuối cùng (sau khi gỡ ẩn danh nếu có):\n{result}")
        return result

    def _model_structure_repr(self, model: Type[BaseModel]) -> str:
        fields = model.__annotations__
        return ', '.join(f'{key}: {value}' for key, value in fields.items())

    def _is_valid_json_for_model(self, text: str, model: Type[BaseModel]) -> bool:
        model.model_config = ConfigDict(strict=True)
        try:
            parsed_data = json.loads(text)
            model(**parsed_data)
            return True
        except (json.JSONDecodeError, ValidationError) as e:
            print(f"❌ Validation failed: {e}")
            return False
