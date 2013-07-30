from pandaviz.models import base


def includeme(config):
    config.scan("pandaviz.models")
    base.Base.metadata.bind = config.registry.db_engine
    base.Base.metadata.create_all(config.registry.db_engine)
