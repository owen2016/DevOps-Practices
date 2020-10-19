#!/bin/python
# -*- coding: utf-8 -*-

#出现异常时，用钉钉dingtalk报警

from flask import Flask
from flask import request
import json
import requests

app = Flask(__name__)

def transform(text):
    textMap = json.loads(text)

    nodePorturl = 'http://192.168.10.182:3672'
    externalURL = textMap['externalURL']
    print(externalURL)
    links =[]
    for alert in textMap['alerts']:
        print('-------------')
        time = alert['startsAt'] + ' -- ' + alert['endsAt']
        generatorURL = alert['generatorURL'];
        generatorURL = nodePorturl+generatorURL[generatorURL.index('graph'):]
        summary = alert['annotations']['summary']
        description = alert['annotations']['description']
        status = alert['status']
        title = alert['labels']['alertname']
        link = {}
        link['title'] = title
        link['text'] = status + ': ' + description
        link['messageUrl'] = generatorURL
        link['picUrl'] = ''
        links.append(link)
    return links

@app.route('/',methods=['POST'])
def send():
    if request.method == 'POST':
        post_data = request.get_data()
        alert_data(post_data)
    return "hello"

def alert_data(data):
    url = 'https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN'
    headers = {'Content-Type': 'application/json'}
    for link in transform(data):
        send_data = {"msgtype": "link", "link": link}
        print(send_data)
        r = requests.post(url, data=json.dumps(send_data), headers=headers)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1111)