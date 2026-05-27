import sys
import os

# Add the parent directory to the Python path so we can import 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api.frontier_client import DeepSeekClient

def main():
    print("=== DeepSeek Frontier Model Test ===")
    try:
        client = DeepSeekClient()
    except ValueError as e:
        print(f"\n[ERROR] {e}")
        print("Please copy .env.example to .env and insert your API key.")
        sys.exit(1)

    print("DeepSeek Client successfully initialized.")
    
    # Simple test conversation
    messages = [
        {"role": "system", "content": "You are a concise, helpful AI assistant."},
        {"role": "user", "content": "Hello! What underlying model architecture are you based on? Please keep it to one short sentence."}
    ]
    
    print(f"\nUser: {messages[1]['content']}")
    print("Waiting for DeepSeek response...\n")
    
    try:
        response = client.chat(messages)
        print(f"DeepSeek: {response}")
        print("\n[SUCCESS] Phase 1 Frontier Model API is working perfectly!")
    except Exception as e:
        print(f"\n[ERROR] Failed to communicate with DeepSeek API: {e}")

if __name__ == "__main__":
    main()
