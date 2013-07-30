import bz2
import csv
import io
import itertools
import os
import shutil
import sys
import tarfile
import tempfile
import urllib2

import pandaviz.models.base
from pandaviz import models
from pandaviz import paster


def to_buffer(fh, chunk_size=512 * 1024):
    buf = io.BytesIO()
    while True:
        chunk = fh.read(chunk_size)
        if not chunk:
            break

        buf.write(chunk)
    return buf.getvalue()


def progress_dots(it, interval=10000):
    for index, x in enumerate(it):
        yield x

        if index % interval == 0:
            print ".",

    print


def interval_caller(it, callback, interval=10000):
    for index, x in enumerate(it):
        yield x

        if index % interval == 0:
            callback()


def main():
    # no output buffering
    sys.stdout = os.fdopen(sys.stdout.fileno(), "w", 0)

    env = paster.bootstrap(sys.argv[1])
    registry = env["registry"]
    request = env["request"]

    models.base.Base.metadata.drop_all()
    models.base.Base.metadata.create_all()

    with tempfile.NamedTemporaryFile() as tempfh:
        print "Downloading school list..."
        shutil.copyfileobj(
            urllib2.urlopen(
                "https://docs.google.com/uc?export=download&id=0B7DR8SBFHA1wUkJTQXlxc3hjR28"),
            tempfh)
        tempfh.seek(0)

        school_schema = {
            "name": (15, 100, lambda x: x.decode("iso-8859-1").strip()),
            "census_id": (6, 9, int),
            "muni_ibge_id": (181, 9, int),
        }
        schools_by_census_id = {}

        print "Inserting schools..."
        with tarfile.open(tempfh.name) as tarf:
            for line in progress_dots(tarf.extractfile(tarf.next())):
                school_dict = {
                    k: converter(line[start - 1:start + end - 1])
                    for k, (start, end, converter) in school_schema.iteritems()}
                if school_dict["muni_ibge_id"] == 3550308:  # sampa only
                    school = models.School(
                        census_id=school_dict["census_id"], name=school_dict["name"])
                    schools_by_census_id[school.census_id] = school
                    request.db.add(school)

    with tempfile.NamedTemporaryFile() as tempfh:
        print "Downloading student list..."
        shutil.copyfileobj(
            urllib2.urlopen(
                "https://docs.google.com/uc?export=download&id=0B7DR8SBFHA1wTHNuWmM2ZUl2RUU"),
            tempfh)
        tempfh.seek(0)

        student_schema = {
            "census_id": (1, 12, int),
            "score_math": (
                564, 9, lambda x: float(x.replace(",", ".")) if x.strip() != "." else None),
            "school_census_id": (204, 8, int),
        }

        print "Inserting students..."
        with bz2.BZ2File(tempfh.name) as fh:
            for line in interval_caller(progress_dots(fh), request.db.flush):
                student_dict = {
                    k: converter(line[start - 1:start + end - 1])
                    for k, (start, end, converter) in student_schema.iteritems()}

                if student_dict["school_census_id"] not in schools_by_census_id:
                    continue

                student = models.Student(
                    census_id=student_dict["census_id"], score_math=student_dict["score_math"])
                student.school = schools_by_census_id[student_dict["school_census_id"]]
                request.db.add(student)

    print "Committing... (this includes trigger and index updates)"
    request.db.commit()

    print "Vacuuming... (optimizes FT queries)"
    registry.db_engine.connect().execution_options(isolation_level="AUTOCOMMIT").execute("VACUUM;")


if __name__ == "__main__":
    import pandaviz.scripts.loadimportdata
    pandaviz.scripts.loadimportdata.main()
