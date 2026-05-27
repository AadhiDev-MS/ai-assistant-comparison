import chromadb
import uuid
import os

class ConversationMemory:
    def __init__(self, max_short_term_messages=4, db_path="app/shared/chroma_db", system_prompt=None):
        """
        Maintains conversational history using a hybrid approach:
        1. Short-term memory (last N messages) for conversational flow.
        2. Long-term memory (ChromaDB RAG) for semantic retrieval of old context.
        """
        self.max_short_term_messages = max_short_term_messages
        
        # Base system prompt
        default_prompt = "You are a concise, helpful AI assistant. Answer in 2-3 sentences max."
        self.base_system_prompt_content = system_prompt if system_prompt else default_prompt
        
        self.short_term_history = []
        
        # Initialize Vector DB (Portable)
        os.makedirs(db_path, exist_ok=True)
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        
        # Create a collection for this conversation session (using a random UUID to avoid conflicts if restarted)
        self.session_id = str(uuid.uuid4())
        self.collection = self.chroma_client.get_or_create_collection(name=f"chat_{self.session_id}")
        self.msg_count = 0

    def add_user_message(self, message):
        self.short_term_history.append({"role": "user", "content": message})
        self._save_to_vector_db("user", message)
        self._trim_short_term()

    def add_assistant_message(self, message):
        self.short_term_history.append({"role": "assistant", "content": message})
        self._save_to_vector_db("assistant", message)
        self._trim_short_term()

    def _save_to_vector_db(self, role, content):
        """Saves a message to ChromaDB for long-term semantic retrieval."""
        self.msg_count += 1
        self.collection.add(
            documents=[content],
            metadatas=[{"role": role, "timestamp": self.msg_count}],
            ids=[f"msg_{self.msg_count}"]
        )

    def get_messages(self, current_prompt=None):
        """
        Reconstructs the prompt context using RAG.
        If a current_prompt is provided, it searches the Vector DB for related past messages.
        """
        system_content = self.base_system_prompt_content
        
        # 1. RAG Retrieval (Long-Term Memory)
        if current_prompt and self.msg_count > self.max_short_term_messages:
            try:
                results = self.collection.query(
                    query_texts=[current_prompt],
                    n_results=3 # Get top 3 most relevant past messages
                )
                
                if results and results['documents'] and len(results['documents'][0]) > 0:
                    retrieved_context = "\\n\\n--- RELEVANT CONTEXT FROM PAST CONVERSATION ---\\n"
                    for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
                        retrieved_context += f"- [{metadata['role']}]: {doc}\\n"
                    
                    system_content += retrieved_context
            except Exception as e:
                pass # Fail silently if DB errors, just use short-term memory
                
        messages = [{"role": "system", "content": system_content}]
        
        # 2. Add Short-Term Memory (Conversational Flow)
        messages.extend(self.short_term_history)
        
        return messages

    def _trim_short_term(self):
        # Keep only the most recent N messages for flow
        if len(self.short_term_history) > self.max_short_term_messages:
            self.short_term_history = self.short_term_history[-self.max_short_term_messages:]
