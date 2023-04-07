from .chat_routes import *
from package.chatgpt.gpt import *
from init import *

@chat_bp.route('/textchat', methods=['POST'])
def handle_chat_textchat():
    # 用户聊天
    # ...
    api_key = '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'
    prompt = '请帮忙输出一篇文章'
    response = gpt_content(api_key, prompt)
    print(response)
    print(response['choices'][0]['text'])

    return f'handle_chat_textchat: 100\nresponse:{response}'
