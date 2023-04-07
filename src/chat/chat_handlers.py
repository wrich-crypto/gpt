from .chat_routes import *
from package.chatgpt.gpt import *
from init import *

@chat_bp.route('/textchat')
def handle_chat_textchat():
    # 用户聊天
    # ...
    api_key = ''
    response = gpt_content(api_key)

    return f'User count: 100\nresponse:{response}'
