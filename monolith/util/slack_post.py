from slacker import Slacker

def postData(api_token, message, channel):
    try:
        if api_token != '':
            slack = Slacker(api_token)
            slack.chat.post_message(
                channel,
                message,
                as_user=True
            )
            return True
        else:
            return False
    except:
        return False
