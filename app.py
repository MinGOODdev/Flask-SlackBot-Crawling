# -*- coding: utf-8 -*-
import json
import urllib.request

from bs4 import BeautifulSoup
from flask import Flask, request, make_response
from slackclient import SlackClient

import config

app = Flask(__name__)

slack_token = config.SLACK_TOKEN
slack_client_id = config.SLACK_CLIENT_ID
slack_client_secret = config.SLACK_CLIENT_SECRET
slack_verification = config.SLACK_VERIFICATION
sc = SlackClient(slack_token)


def _crawl_bugs_keywords(text):
    url = "https://music.bugs.co.kr/chart"
    soup = BeautifulSoup(urllib.request.urlopen(url).read(), "html.parser")

    keywords = []

    for table in soup.find_all("table", class_="list trackList byChart"):
        for tr in table.find_all("tr"):
            string = ''
            for strong in tr.find_all("strong"):
                string += strong.get_text() + "위: "
            for p in tr.find_all("p", class_="title"):
                string += p.find("a")["title"] + " / "
            for p in tr.find_all("p", class_="artist"):
                string += p.find("a")["title"]

            if len(keywords) <= 10:
                keywords.append(string)

    # 한글 지원을 위해 앞에 unicode u를 붙혀준다.
    return u'\n'.join(keywords)


def _event_handler(event_type, slack_event):
    print(slack_event["event"])

    if event_type == "app_mention":
        channel = slack_event["event"]["channel"]
        text = slack_event["event"]["text"]

        keywords = _crawl_bugs_keywords(text)
        sc.api_call(
            "chat.postMessage",
            channel=channel,
            text=keywords
        )
        return make_response("App mention message has been sent", 200)

    message = "You have not added an event handler for the %s" % event_type

    return make_response(message, 200, {"X-Slack-No-Retry": 1})


@app.route("/listening", methods=["GET", "POST"])
def hears():
    slack_event = json.loads(request.data)

    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"content_type": "application/json"})

    if slack_verification != slack_event.get("token"):
        message = "Invalid Slack verification token: %s" % (slack_event["token"])
        make_response(message, 403, {"X-Slack-No-Retry": 1})

    if "event" in slack_event:
        event_type = slack_event["event"]["type"]
        return _event_handler(event_type, slack_event)

    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\ you're looking for.", 404,
                         {"X-Slack-No-Retry": 1})


@app.route("/")
def index():
    return "<h1>MinGOODdev SlackBot.</h1>"


if __name__ == '__main__':
    app.run()
