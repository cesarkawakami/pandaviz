import sys

import pyramid.paster

from pandaviz import paster


def bootstrap_gevent(server):
    import gevent.monkey
    import psycogreen.gevent
    gevent.monkey.patch_all()
    psycogreen.gevent.patch_psycopg()


def main():
    config_path = sys.argv[1]
    pyramid.paster.setup_logging(config_path)
    app = paster.get_app(config_path)
    server = paster.get_server(config_path)
    server(app)


if __name__ == "__main__":
    import pandaviz.run
    pandaviz.run.main()
