import requests
import time

class OSSClient:
    def __init__(self, host_ip="127.0.0.1"):
        """
        Connects to the Ollama server.
        """
        self.base_url = f"http://{host_ip}:11434/api/chat"

    def chat(self, messages):
        payload = {
            "model": "llama3.2", # Make sure this matches the model we pull on the server
            "messages": messages,
            "stream": False
        }
        
        try:
            start_time = time.time()
            # We give it a generous timeout since 8B models can take a moment to generate long responses
            response = requests.post(self.base_url, json=payload, timeout=120)
            response.raise_for_status()
            
            latency_ms = (time.time() - start_time) * 1000
            data = response.json()
            
            content = data["message"]["content"]
            
            # Extract Ollama token metrics
            prompt_tokens = data.get("prompt_eval_count", 0)
            completion_tokens = data.get("eval_count", 0)
            total_tokens = prompt_tokens + completion_tokens
            
            # Since we host it ourselves, the API cost per token is $0.00!
            # (We only pay the flat $0.52/hr AWS fee)
            cost_usd = 0.0
            
            return {
                "content": content,
                "latency_ms": latency_ms,
                "total_tokens": total_tokens,
                "cost_usd": cost_usd
            }
        except requests.exceptions.RequestException as e:
            print(f"OSS API Error: {e}")
            raise e

    def chat_stream(self, messages):
        """
        Connects to Ollama and yields the response as a stream of tokens.
        """
        payload = {
            "model": "llama3.2",
            "messages": messages,
            "stream": True
        }
        
        response = requests.post(self.base_url, json=payload, stream=True)
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                try:
                    import json
                    data = json.loads(line.decode('utf-8'))
                    if "message" in data and "content" in data["message"]:
                        yield data["message"]["content"]
                except json.JSONDecodeError:
                    pass
