from .chat_routes import *
from package.chatgpt.gpt import *
from init import *

@chat_bp.route('/textchat', methods=['POST'])
def handle_chat_textchat():
    prompt = request.form.get('prompt')
    print(f'prompt:{prompt}')

    # api_key = current_app.config.get('API_KEY')
    api_key = ''

    # 用户聊天
    response = gpt_content(api_key, prompt)
    print(response)

    response_data = ErrorCode.success({'response': response})

    return jsonify(response_data)
