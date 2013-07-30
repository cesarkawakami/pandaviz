import sqlalchemy
import sqlalchemy.orm


def db(request):
    session = request.registry.db_sessionmaker()
    request.add_finished_callback(lambda request: session.close())
    return session


def includeme(config):
    engine = sqlalchemy.engine_from_config(config.registry.settings, prefix="sqlalchemy.")
    config.registry.db_engine = engine
    config.registry.db_sessionmaker = sqlalchemy.orm.sessionmaker(bind=engine)
    config.add_request_method(db, reify=True)
