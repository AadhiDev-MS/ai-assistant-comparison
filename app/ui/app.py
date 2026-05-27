import gradio as gr
import sys
import os

# Add parent directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api.frontier_client import DeepSeekClient
from app.api.oss_client import OSSClient
from app.shared.memory import ConversationMemory
from app.shared.logger import InteractionLogger

# Initialize API clients, memory, and database logger
logger = InteractionLogger()

try:
    frontier_client = DeepSeekClient()
except ValueError as e:
    print(f"Failed to initialize DeepSeek: {e}")
    frontier_client = None

try:
    oss_client = OSSClient()
except Exception as e:
    print(f"Failed to initialize OSS Client: {e}")
    oss_client = None

frontier_memory = ConversationMemory()
oss_memory = ConversationMemory()  # Ready for when our AWS server comes online!

def process_chat(user_message, frontier_history, oss_history):
    """
    Handles a single chat turn. Sends the message to both models and updates the UI.
    """
    # 1. Update internal memory for both models
    frontier_memory.add_user_message(user_message)
    oss_memory.add_user_message(user_message)

    # 2. Get Frontier Model Response (DeepSeek)
    if frontier_client:
        try:
            response_data = frontier_client.chat(frontier_memory.get_messages())
            frontier_response = response_data["content"]
            frontier_memory.add_assistant_message(frontier_response)
            
            # Log the telemetry data to our SQLite DB
            logger.log_interaction(
                model_name="DeepSeek v4 Pro",
                prompt=user_message,
                response=frontier_response,
                latency_ms=response_data["latency_ms"],
                total_tokens=response_data["total_tokens"],
                cost_usd=response_data["cost_usd"]
            )
        except Exception as e:
            frontier_memory.add_assistant_message(f"API Error: {e}")
    else:
        frontier_memory.add_assistant_message("DeepSeek API key not configured.")

    # 3. Get OSS Model Response (AWS EC2)
    if oss_client:
        try:
            oss_response_data = oss_client.chat(oss_memory.get_messages())
            oss_response = oss_response_data["content"]
            oss_memory.add_assistant_message(oss_response)
            
            # Log the telemetry data
            logger.log_interaction(
                model_name="Llama 3.2 8B (AWS)",
                prompt=user_message,
                response=oss_response,
                latency_ms=oss_response_data["latency_ms"],
                total_tokens=oss_response_data["total_tokens"],
                cost_usd=oss_response_data["cost_usd"]
            )
        except Exception as e:
            oss_memory.add_assistant_message(f"API Error (Is the AWS server running Ollama?): {e}")
    else:
        oss_memory.add_assistant_message("OSS API Client failed to initialize.")

    # 4. Reconstruct UI history directly from our memory to prevent Gradio formatting bugs
    def format_for_ui(memory_instance):
        return [
            {"role": msg["role"], "content": msg["content"]} 
            for msg in memory_instance.get_messages() 
            if msg["role"] != "system"
        ]

    return "", format_for_ui(frontier_memory), format_for_ui(oss_memory)

# Build the beautiful Gradio UI
with gr.Blocks(title="AI Assistant Comparison") as demo:
    gr.Markdown("# 🚀 AI Assistant Comparison Studio (v2)")
    gr.Markdown("Compare an open-source model running on **AWS EC2** against **DeepSeek v4 Pro** in real-time.")
    
    with gr.Tabs():
        with gr.Tab("💬 Chat Studio"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### 🌟 Frontier Model (DeepSeek v4 Pro)")
                    frontier_chatbot = gr.Chatbot(height=500)
                    
                with gr.Column():
                    gr.Markdown("### ☁️ Open Source Model (AWS EC2)")
                    oss_chatbot = gr.Chatbot(height=500)
                    
            with gr.Row():
                msg_input = gr.Textbox(placeholder="Type your prompt here...", scale=4)
                submit_btn = gr.Button("Send", scale=1, variant="primary")

            # Tie the input and button to the processing function
            submit_btn.click(
                fn=process_chat,
                inputs=[msg_input, frontier_chatbot, oss_chatbot],
                outputs=[msg_input, frontier_chatbot, oss_chatbot]
            )
            msg_input.submit(
                fn=process_chat,
                inputs=[msg_input, frontier_chatbot, oss_chatbot],
                outputs=[msg_input, frontier_chatbot, oss_chatbot]
            )
            
        with gr.Tab("📊 Observability Dashboard"):
            gr.Markdown("### Real-time Telemetry & Costs")
            gr.Markdown("*Tracking all interactions to fulfill the 'Cost + Latency Table' bonus requirement.*")
            
            refresh_btn = gr.Button("🔄 Refresh Data")
            log_table = gr.Dataframe(
                headers=["Timestamp", "Model", "Latency (ms)", "Tokens", "Cost ($)", "Prompt", "Response"],
                datatype=["str", "str", "number", "number", "number", "str", "str"],
                interactive=False,
                wrap=True
            )
            
            def load_logs():
                return logger.get_logs_as_list()
                
            refresh_btn.click(fn=load_logs, inputs=[], outputs=[log_table])
            demo.load(fn=load_logs, inputs=[], outputs=[log_table])

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860, theme=gr.themes.Soft())
