import setuptools


setuptools.setup(
    name="pandaviz",
    version="0.1",
    url="http://www.geekie.com.br",
    maintainer="Cesar Kawakami",
    maintainer_email="cesar@geekie.com.br",
    packages=["pandaviz"],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "gevent==0.13.8",
        "gunicorn==17.5",
        "pastedeploy==1.5.0",
        "pyramid==1.4.3",
        "sqlalchemy==0.8.2",
        "psycopg2==2.5.1",
        "psycogreen==1.0",
        "pyramid-beaker==0.8",
    ],
    entry_points={
        "paste.app_factory": "main = pandaviz.app:create_app",
        "paste.server_factory": "gevent = pandaviz.server:create_server",
    },
)
