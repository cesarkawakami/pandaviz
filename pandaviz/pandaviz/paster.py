import os

import paste.deploy

import pyramid.scripting


def uri_for(config_path):
    return "config:" + config_path


def get_app(config_path):
    return paste.deploy.loadapp(
        uri_for(config_path), relative_to=os.getcwd(), global_conf=os.environ)


def get_server(config_path):
    return paste.deploy.loadserver(
        uri_for(config_path), relative_to=os.getcwd(), global_conf=os.environ)


def bootstrap(config_path, request=None):
    app = get_app(config_path)
    env = pyramid.scripting.prepare(request, registry=app.registry)
    env["app"] = app
    return env
