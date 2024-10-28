# appsvc

appsvc is an apps management service

## release a new version

Inside a devcontainer:

    make lint
    make build

Outside of a devcontainer:

    make docker-build
    make docker-run
    make docker-pub TAG=0.0.1
