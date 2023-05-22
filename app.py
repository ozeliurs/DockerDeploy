import json
from pathlib import Path

from flask import Flask, request

from docker import DockerClient

app = Flask(__name__)

# docker_client = DockerClient(base_url='unix://var/run/docker.sock')


@app.post('/')
def webhook():
    # Check if the request is an event
    if 'X-GitHub-Event' not in request.headers or request.headers['X-GitHub-Event'] != 'package':
        return 'No package event'

    # Check if the action is related to a package been published or updated
    if 'action' not in request.json or request.json['action'] not in ['published', 'updated']:
        return 'No action required'

    image_url = request.json['package']['package_version']['package_url']
    image_name = image_url.split('/')[-1].split(':')[0]
    image_tag = image_url.split('/')[-1].split(':')[1]

    print(f"Received package {image_name}:{image_tag} at {image_url}")

    return 'OK'


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
