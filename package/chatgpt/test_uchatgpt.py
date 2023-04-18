from uchatgpt import *

def test_chat_api():
    access_token = ""
    chat_api = ChatAPI(access_token)

    # # Test ask() method
    # try:
    #     response = chat_api.ask("猫有多少种？")
    #     print(response)
    # except Exception as e:
    #     print(f"Test failed: {e}")

    # Test create_stream() and get_stream() methods
    try:
        create_stream_response = chat_api.create_stream("猫有多少种？")
        print(create_stream_response)

        stream_id = create_stream_response["data"]["streamId"]
        stream_response = chat_api.get_stream(stream_id)
        print(stream_response.text)
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_chat_api()
