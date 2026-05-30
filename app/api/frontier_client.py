import os
import requests
from dotenv import load_dotenv

load_dotenv()

class DeepSeekClient:
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY is not set in the environment. Please create a .env file and add it.")
        self.base_url = "https://api.deepseek.com/chat/completions"

    def chat(self, messages, temperature=0.7):
        """
        Sends a conversation history to DeepSeek and returns the response.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",  # The general chat/reasoning model
            "messages": messages,
            "temperature": temperature
        }
        
        try:
            import time
            start_time = time.time()
            
            response = requests.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
            
            latency_ms = (time.time() - start_time) * 1000
            data = response.json()
            
            content = data["choices"][0]["message"]["content"]
            total_tokens = data.get("usage", {}).get("total_tokens", 0)
            
            # DeepSeek v4 Pro blended average cost estimation (~$0.27 per 1M tokens)
            cost_usd = (total_tokens / 1_000_000) * 0.27
            
            return {
                "content": content,
                "latency_ms": latency_ms,
                "total_tokens": total_tokens,
                "cost_usd": cost_usd
            }
        except requests.exceptions.RequestException as e:
            print(f"API Error details: {response.text if 'response' in locals() else 'No response'}")
            raise e

    def chat_stream(self, messages, temperature=0.7):
        """
        Sends a conversation history to DeepSeek and yields the response as a stream of tokens.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": messages,
            "temperature": temperature,
            "stream": True
        }
        
        response = requests.post(self.base_url, headers=headers, json=payload, stream=True)
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        import json
                        data = json.loads(data_str)
                        if "choices" in data and len(data["choices"]) > 0:
                            delta = data["choices"][0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]
                    except json.JSONDecodeError:
                        pass
