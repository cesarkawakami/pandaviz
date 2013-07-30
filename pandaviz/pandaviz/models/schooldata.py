import sqlalchemy
import sqlalchemy.event
import sqlalchemy.orm

from pandaviz.models import base


TEXT_SEARCH_CONFIG_NAME = "plain_ts_config"
TEXT_SEARCH_DICT_NAME = "plain_ts_dict"


class School(base.Base):

    __tablename__ = "schools"

    id_ = sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True)
    census_id = sqlalchemy.Column(sqlalchemy.Integer, unique=True)
    name = sqlalchemy.Column(sqlalchemy.Unicode(100))

    students = sqlalchemy.orm.relationship("Student", backref="school")

    def __init__(self, census_id=-1, name=u""):
        self.census_id = census_id
        self.name = name

    @classmethod
    def name_tsvector(cls):
        return sqlalchemy.func.to_tsvector(TEXT_SEARCH_CONFIG_NAME, cls.name)

    @classmethod
    def tsquerize(cls, text):
        return sqlalchemy.func.to_tsquery(TEXT_SEARCH_CONFIG_NAME, text)


class Student(base.Base):

    __tablename__ = "students"

    id_ = sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True)
    census_id = sqlalchemy.Column(sqlalchemy.BigInteger, unique=True)
    score_math = sqlalchemy.Column(sqlalchemy.Float)
    school_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("schools.id"), index=True)

    def __init__(self, census_id=-1, score_math=0.0):
        self.census_id = census_id
        self.score_math = score_math


sqlalchemy.event.listen(
    School.__table__,
    "after_create",
    sqlalchemy.DDL(
        """
        DROP TEXT SEARCH CONFIGURATION IF EXISTS %(tsconfig)s;
        DROP TEXT SEARCH DICTIONARY IF EXISTS %(tsdict)s;
        DROP EXTENSION IF EXISTS unaccent;

        CREATE EXTENSION IF NOT EXISTS unaccent;
        CREATE TEXT SEARCH DICTIONARY %(tsdict)s (
            TEMPLATE = pg_catalog.simple
        );
        CREATE TEXT SEARCH CONFIGURATION %(tsconfig)s (PARSER = pg_catalog.default);
        ALTER TEXT SEARCH CONFIGURATION %(tsconfig)s
            ALTER MAPPING FOR asciiword, asciihword, hword_asciipart, word, hword, hword_part
            WITH unaccent, %(tsdict)s;

        CREATE INDEX idx_school_names ON schools USING gin(to_tsvector('%(tsconfig)s', name));
        """,
        context=dict(tsconfig=TEXT_SEARCH_CONFIG_NAME, tsdict=TEXT_SEARCH_DICT_NAME)
    ).execute_if(dialect="postgresql"),
)
