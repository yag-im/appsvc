#!/usr/bin/env bash

mkdir -p /workspaces/appsvc/.vscode
cp /workspaces/appsvc/.devcontainer/vscode/* /workspaces/appsvc/.vscode

make bootstrap
