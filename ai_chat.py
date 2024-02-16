from openai import OpenAI, RateLimitError


class OpenAIChat():
    __slots__ = ['__client']

    def __init__(self, openai_token):
        self.__client = OpenAI(api_key=openai_token)

    def get_response(self, message_request):
        try:
            response = self.__client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": message_request}],
                stream=False,
            )
            return response['choices'][0]['message']['content']
        except RateLimitError as e:
            print(f"Rate limit exceeded. Please check your OpenAI plan and usage. Details: {e}")
            return None

