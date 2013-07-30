import pyramid.config

import pyramid_beaker


def create_app(global_config, **settings):
    pyramid_beaker.set_cache_regions_from_settings(settings)

    config = pyramid.config.Configurator(settings=settings)

    config.add_static_view(name="static", path="pandaviz.www:static")

    config.include("pandaviz.db")
    config.include("pandaviz.models.init")

    config.include("pandaviz.www.home")
    config.scan("pandaviz.www")

    return config.make_wsgi_app()
