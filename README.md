# AI Assistant Comparison Studio: Frontier vs. Open Source

A full-stack AI evaluation platform built to compare the performance, safety, and latency of Frontier APIs (DeepSeek v4 Pro) against self-hosted Open Source models (Llama 3.2 8B) in real-time. 

This project fulfills all core requirements and bonus objectives for the AI Personal Assistant engineering challenge.

![Dashboard Preview](app/frontend/assets/dashboard_preview.png) *(Preview of the UI)*

---

## 🏗️ Architecture Decisions

The system is built with a decoupled architecture prioritizing real-time streaming, concurrent processing, and strict safety guardrails.

**1. Backend (FastAPI)**
- **Concurrent Streaming:** The monolithic chat endpoint was split into three independent asynchronous routes (`/api/chat/deepseek`, `/api/chat/oss`, `/api/chat/oss_secure`) returning Server-Sent Events (SSE). This allows the UI to stream tokens from all three models simultaneously.
- **RAG Vector Memory:** Implemented ChromaDB to handle short-term conversational context. User prompts are vectorized and semantically matched against recent history before being injected into the LLM context window.
- **Telemetry Logger:** A local SQLite database tracks Time-to-First-Token (TTFT), Tokens-Per-Second (TPS), and Cost-per-query.

**2. Frontend (Vanilla JS + HTML/CSS)**
- **Zero-Dependency Core:** Built using pure Vanilla JavaScript to demonstrate strong fundamental web development skills without relying on heavy frameworks like React.
- **ReadableStreams API:** Implemented native JavaScript `ReadableStream` readers and `TextDecoder` to parse the incoming byte-chunks and re-render Markdown dynamically in real-time.

**3. Infrastructure (AWS EC2)**
- **Self-Hosted OSS:** Deployed Llama 3.2 8B on an AWS `g4dn.xlarge` instance using Ollama to fulfill the public deployment requirement and provide a baseline for API vs Self-hosted latency comparisons.

**4. Safety & Guardrails (Constitutional AI)**
- To test safety, the OSS model was duplicated into two instances: "Unfiltered" and "Secured". 
- The "Secured" instance is wrapped in a strict System Prompt enforcing Adversarial Immunity, Anti-Stereotyping, and standardized refusal formats.

---

## ⚖️ Tradeoffs Made

1. **Self-Hosted GPU vs Managed API:** 
   We chose to deploy Llama 3.2 on a single AWS T4 GPU (`g4dn.xlarge`). While highly cost-effective, running two concurrent OSS requests (Unfiltered + Secured) against the same T4 GPU creates a compute bottleneck, resulting in higher TTFT (~1-3s) and lower TPS (~15-20) compared to DeepSeek's optimized H100 clusters. This highlights the classic tradeoff between data privacy (self-hosted) and raw speed (managed API).
   
2. **Vanilla JS vs React/Next.js:**
   We opted for Vanilla JS to keep the frontend incredibly lightweight and fast. However, the tradeoff is manual DOM manipulation (e.g., continually updating `innerHTML` for markdown rendering during the SSE stream), which becomes difficult to scale if the UI complexity increases.

3. **Token Approximation:**
   Because the models stream raw text chunks without usage metadata attached to every packet, we implemented a heuristic token approximation (`1 word ≈ 1.3 tokens`) to calculate TPS and costs dynamically. While standard for streaming UIs, a more robust solution would involve running a local `tiktoken` encoder on the server.

---

## 🔮 Future Improvements

If given more time, I would improve the following:

1. **vLLM Integration:** Replace the basic Ollama runner on AWS with `vLLM` to achieve significantly higher Tokens-Per-Second and better concurrent request batching for the OSS models.
2. **PostgreSQL Migration:** Move the local SQLite telemetry database to a hosted PostgreSQL instance (e.g., Supabase) to enable cross-device dashboard analytics.
3. **Advanced RAG:** Upgrade the ChromaDB implementation to include hybrid search (BM25 + Dense Vectors) and document upload capabilities, allowing users to chat with PDFs.
4. **Automated Red-Teaming:** Expand the current Python evaluation harness to utilize an "LLM-as-a-Judge" architecture, where a frontier model automatically scores the safety and bias of the OSS model's outputs.

---

## 🚀 Setup Instructions

### Prerequisites
- Python 3.10+
- DeepSeek API Key
- A running Ollama server (local or AWS)

### Installation
1. **Clone the repository**
   ```bash
   git clone https://github.com/AadhiDev-MS/ai-assistant-comparison.git
   cd ai-assistant-comparison
   ```

2. **Set up the Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**
   Create a `.env` file in the root directory:
   ```env
   DEEPSEEK_API_KEY="your_api_key_here"
   ```
   *Note: Ensure your AWS EC2 IP address is updated in `app/api/oss_client.py` if running a remote Ollama server.*

5. **Start the Server**
   ```bash
   python -m app.backend.server
   ```
   Navigate to `http://127.0.0.1:8000` to access the application.
