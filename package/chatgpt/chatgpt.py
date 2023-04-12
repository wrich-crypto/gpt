from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain import OpenAI, LLMChain, PromptTemplate

class ChatManager:
    def __init__(self):
        self.channels = {}

    def get_channel(self, channel_id, api_key):
        if channel_id not in self.channels:
            self.channels[channel_id] = self.create_llm_chain(api_key)
        return self.channels[channel_id]

    @staticmethod
    def create_llm_chain(api_key):
        template = """You are a chatbot having a conversation with a human.

                {chat_history}
                Human: {human_input}
                Chatbot:"""

        prompt = PromptTemplate(
            input_variables=["chat_history", "human_input"],
            template=template
        )
        memory = ConversationBufferMemory(memory_key="chat_history")

        llm_chain = LLMChain(
            llm=OpenAI(openai_api_key=api_key, temperature=0.7),
            prompt=prompt,
            verbose=True,
            memory=memory,
        )

        return llm_chain

def handle_chat(chat_manager, channel_id, user_input, api_key):
    try:
        times = 1
        llm_chain = chat_manager.get_channel(channel_id, api_key)
        response = llm_chain.predict(human_input=user_input)
        return response, (500 * times), None
    except Exception as e:
        return '', 0, str(e)
