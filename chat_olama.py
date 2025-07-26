import requests

def chat_with_ollama(prompt: str, model: str = "mistral:latest", base_url: str = "http://localhost:11434"):
    url = f"{base_url}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False  # Không cần stream để đơn giản hóa
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json().get("response", "")
    except requests.RequestException as e:
        return f"Request failed: {e}"
    except ValueError:
        return "Invalid response received from the model."

# Ví dụ sử dụng:
if __name__ == "__main__":
    user_input = "Write a CV for me and use expactly identify infomation: My name is Alice Johnson, "
    "email: alice.johnson@example.com, phone: +1 234-567-8910. "
    "I am a machine learning engineer."
    answer = chat_with_ollama(user_input)
    print("Model response:", answer)
