# appsvc

appsvc is an apps management service. Implements logic for apps search, start/stop, pause/resume.

## Development

### Prerequisite

Create *.devcontainer/secrets.env* file:

    SQLDB_PASSWORD=***VALUE***

Change `STREAMD_REQS` parameter in *.devcontainer/.env* file:

    - set `igpu` to true if you want to use integrated GPU (Intel HD) for video encoding
    - set `dpgu` to true if you want to use dedicated GPU (Nvidia) for video encoding

The following devcontainers should be up and running:

    sqldb

Then simply open this project in any IDE that supports devcontainers (VSCode is recommended).
