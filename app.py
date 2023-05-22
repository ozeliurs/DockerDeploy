import uuid
from pathlib import Path

from docker.errors import NotFound
from flask import Flask, request

from docker import DockerClient

app = Flask(__name__)

logs = Path('logs')
logs.mkdir(exist_ok=True)


def log(message, run_identifier):
    with open(logs / f'{run_identifier}.log', 'a') as f:
        f.write(f'{message}\n')


try:
    docker_client = DockerClient(base_url='unix://var/run/docker.sock')
except Exception as e:
    print(f"Failed to connect to the Docker daemon: {e}")
    exit(1)


@app.get('/')
def index():
    return "<br>".join([f"<a href=\"/{log}\">{log}</a>" for log in logs.iterdir() if log.is_file() and log.suffix == '.log'])


@app.get('/logs/<run_identifier>')
def get_log(run_identifier):
    if not (logs / f'{run_identifier}').is_file():
        return f"Log {run_identifier} not found"

    if not run_identifier.endswith('.log'):
        return f"Invalid log {run_identifier}"

    try:
        with open(logs / f'{run_identifier}.log', 'r') as f:
            return f.read()
    except Exception as e:
        return f"Failed to read log: {e}"


@app.post('/')
def webhook():
    # Check if the request is an event
    if 'X-GitHub-Event' not in request.headers or request.headers['X-GitHub-Event'] != 'package':
        return 'No package event'

    # Check if the action is related to a package been published or updated
    if 'action' not in request.json or request.json['action'] not in ['published', 'updated']:
        return 'No action required'

    image_url = request.json['package']['package_version']['package_url']
    image_url = image_url.split(':')[0]
    identifier = image_url.split('/')[-1].replace(':', '_')
    run_identifier = str(uuid.uuid4())

    log(f"Received request for {image_url}", run_identifier)

    # If the container already exists, remove it
    try:
        container = docker_client.containers.get(identifier)
    except NotFound:
        container = None

    if container:
        log(f"Removing container {identifier}", run_identifier)
        container.remove(force=True)

    # Run the image
    log(f"Running image {image_url}", run_identifier)
    container = docker_client.containers.run(
        image=image_url,
        name=uuid.uuid4(),
        detach=True,
        restart_policy={'Name': 'unless-stopped'},
        networks=['traefik'],
        labels={
            'traefik.enable': 'true',
            f"traefik.http.routers.{identifier}.rule": f'Host(`{identifier}.dd.ozeliurs.com`)',
            f"traefik.http.routers.{identifier}.entrypoints": 'websecure',
            f"traefik.http.routers.{identifier}.tls.certresolver": 'letsencrypt',
            'traefik.http.routers.docker-deploy.tls': 'true'
        }
    )

    if not container:
        log(f"Failed to run image {image_url}", run_identifier)
        return 'NOK'

    log(f"Successfully ran image {image_url}", run_identifier)
    log(f"Available at https://{identifier}.dd.ozeliurs.com", run_identifier)
    return 'OK'


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
