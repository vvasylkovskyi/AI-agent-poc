from llm.openai_client import OpenAIClient

class KubernetesAgent:
    def __init__(self):
        self.client = OpenAIClient()
        self.history = [
            {"role": "system", "content": "You are an AI specialized in Kubernetes. Answer user questions clearly and concisely."}
        ]

    def get_answer(self, question: str) -> str:
        # Add user's question to history
        self.history.append({"role": "user", "content": question})
        answer = self.client.inference(self.history)
        # Add AI's response to history
        self.history.append({"role": "assistant", "content": answer})
        
        return answer