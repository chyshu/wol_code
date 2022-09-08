from flask import Flask, request, abort
from django.views.decorators.csrf import csrf_exempt

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

app = Flask(__name__)

#line_bot_api = LineBotApi('JsxDdLf5cuphuUVuoGvujchNKUIXJ8EtPC8t9A2ScfS9CgtMNxshsmelb/DE6SxTm5k5M7W4ZEkwEHM51pAyusK9r7FN1JQJJ83xBs0efkt2gZ9JygTkh4Zpwg4pc48tsSHQMKc3uXwwsNankROK4wdB04t89/1O/w1cDnyilFU=')

#handler = WebhookHandler('6c50569bec91e809674daf78228a4689')

line_bot_api = LineBotApi('FN9aUD1hA2GqE0h4emQWsjyPzIMRIEM+xh6kVHJXjm6weD6F6vxlCOLZo2gC6RLwP9Q+1mHrNhyxyEtA6aj65nZHh+nOSsw0YfvFZ7Bah3x8ioThEKyYB2BiRxZdIN1Ytuv377kryazq922MPnFZJgdB04t89/1O/w1cDnyilFU=')

handler = WebhookHandler('a14a4b0d0561b02fb44f4501e6dbd5a3')


# @app.route("/callback", methods=['POST'])

@csrf_exempt
def goMessage():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))


if __name__ == "__main__":
    app.run()
