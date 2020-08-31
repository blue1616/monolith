from slacker import Slacker

def postData(api_token, message, channel):
    slack = Slacker(api_token)
    slack.chat.post_message(
        channel,
        message,
        as_user=True
    )
