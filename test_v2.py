from flask import Flask, request, render_template
from flask_sse import sse
from flask_cors import CORS
import requests

app = Flask(__name__)
app.config["REDIS_URL"] = "redis://"
app.register_blueprint(sse, url_prefix='/stream')
CORS(app)

THIRD_PARTY_API_URL = "https://api.chatuapi.com"

@app.route('/create_stream', methods=['POST'])
def create_stream():
    try:
        print('hi')
        data = request.json
        prompt = data.get("prompt")
        conversation_id = data.get("conversationId", None)

        response = requests.post(f"{THIRD_PARTY_API_URL}/chat/stream/create",
                                 json={"prompt": prompt, "conversationId": conversation_id})

        if response.status_code == 200:
            result = response.json()
            return result
        else:
            return {"code": -1, "message": "Error in creating stream"}, 500
    except Exception as e:
        print(e)

@app.route('/subscribe_stream', methods=['GET'])
def subscribe_stream():
    stream_id = request.args.get('streamId')

    def generate():
        with requests.get(f"{THIRD_PARTY_API_URL}/chat/stream?streamId={stream_id}", stream=True) as response:
            for line in response.iter_lines():
                if line:
                    yield f"data: {line.decode()}\n\n"

    return app.response_class(generate(), content_type='text/event-stream')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
