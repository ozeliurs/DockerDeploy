import json
from pathlib import Path

from flask import Flask, request

from docker import DockerClient

app = Flask(__name__)

# docker_client = DockerClient(base_url='unix://var/run/docker.sock')


@app.post('/')
def webhook():
    # Check if the request is an event
    if 'X-GitHub-Event' not in request.headers and request.headers['X-GitHub-Event'] != 'package':
        return 'No package event'

    # Check if the action is related to a package been published or updated
    if 'action' not in request.json and request.json['action'] not in ['published', 'updated']:
        return 'No action required'

    Path('debug.txt').write_text(json.dumps(request.json))

    # docker_client.images.pull(docker_image)

    return 'Hello World!'


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
