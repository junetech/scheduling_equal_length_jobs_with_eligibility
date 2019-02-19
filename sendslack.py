'''
Slack sending functions
Created in Feb 10th. 2019 by JuneTech
'''

from slackclient import SlackClient


def return_slackclient(slack_json_filename):
    try:
        import json
        with open(slack_json_filename) as json_file:
            slack_data = json.load(json_file)
        sc = SlackClient(slack_data["token"])
    except FileNotFoundError:
        print("No JSON file named:", slack_json_filename)
        raise FileNotFoundError
    except ValueError:
        print("Problem with JSON file named:", slack_json_filename)
        raise ValueError
    except:
        print("Unknown problem reading JSON file named:", slack_json_filename)
        raise EnvironmentError

    return sc, slack_data

def message(sc, slack_data, message_text):
    sc.api_call("chat.postMessage",
                channel=slack_data["im_channel_id"],
                text=message_text,
                as_user=True)
