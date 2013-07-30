import json
import unicodedata

import sqlalchemy

import beaker.cache

import pyramid.decorator
import pyramid.httpexceptions
import pyramid.threadlocal
import pyramid.view

from pandaviz import models


def includeme(config):
    config.add_route("home", pattern="/")
    config.add_route("query", pattern="/query")
    config.add_route("school", pattern="/schools/{id_}")


@pyramid.view.view_config(route_name="home", renderer="templates/main.pt")
def home(request):
    bins = _global_scores()
    return {"bins": json.dumps(bins)}


@pyramid.view.view_config(route_name="query", renderer="json")
def query(request):
    if "q" in request.params and request.params["q"].strip():
        words = request.params["q"]
        words = words.lower()
        words = u"".join(
            c for c in words
            if unicodedata.category(c).startswith("L") or
            unicodedata.category(c) == "Zs")
        words = words.split()

        querylist = []
        for word in words:
            querylist.append(u"({word} | {word}:*)".format(word=word))
        querytext = u" & ".join(querylist)

        school_name_tsvector = models.School.name_tsvector()
        school_name_tsquery = models.School.tsquerize(querytext)

        schools = (
            request.db.query(models.School)
            .filter(school_name_tsvector.op("@@")(school_name_tsquery))
            .order_by(sqlalchemy.desc(sqlalchemy.func.ts_rank(
                school_name_tsvector, school_name_tsquery)))
            .limit(20)
        ).all()
    else:
        schools = []

    schools = [
        {
            "id": x.id_,
            "name": x.name,
            "url": request.route_url("school", id_=x.id_)
        }
        for x in schools
    ]
    return schools


@pyramid.view.view_config(route_name="school", renderer="json")
def school(request):
    school = request.db.query(models.School).get(int(request.matchdict["id_"]))
    students = request.db.query(models.Student).filter_by(school=school).all()
    scores = [x.score_math for x in students if x.score_math is not None]

    return _binize(scores)


@beaker.cache.cache_region("default")
def _global_scores():
    request = pyramid.threadlocal.get_current_request()
    scores = [
        x.score_math for x in request.db.query(models.Student).all() if x.score_math is not None]
    return _binize(scores)


def _binize(numbers):
    n_bins = 20
    min_score = min(numbers)
    max_score = max(numbers) + 0.1
    delta = (max_score - min_score) / n_bins
    bins = [
        {
            "range_min": start,
            "range_max": end,
            "count": sum(1.0 for x in numbers if start <= x < end) / len(numbers),
        }
        for start, end in ((min_score + i * delta, min_score + (i + 1) * delta)
                           for i in xrange(n_bins))
    ]

    return bins
