import io
from operator import attrgetter

import requests
from flask import Flask, abort, url_for
from flask import make_response
from flask import request
from flask_restful import Api, Resource
from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound

DATABASE_URI = 'sqlite:///chinook.db'


def get_pk(table_class):
    table = table_class.__table__
    pk = table.primary_key
    assert len(pk.columns) == 1
    return pk.columns.values()[0]


def get_columns(table_class):
    table = table_class.__table__
    return table.columns.values()


def serialize(obj):
    def convert(value):
        if type(value) in (str, int, float, bool):
            return value
        else:
            return repr(value)

    return {_: convert(getattr(obj, _)) for _ in obj.__table__.columns.keys()}


engine = create_engine(DATABASE_URI)

Base = automap_base()
Base.prepare(engine, reflect=True)
table_classes = sorted(Base.classes, key=attrgetter('__name__'))

session = Session(engine)

# ======================================================================================================================

app = Flask(__name__)
api = Api(app)


class IndexResource(Resource):
    def get(self):
        return [
            dict(
                name=_.__name__,
                url=url_for(_.__name__.lower() + 'resource')
            ) for _ in table_classes]


api.add_resource(IndexResource, '/')


def make_table_resource_class(table_class):
    pk = get_pk(table_class)
    columns = get_columns(table_class)

    def get_object(id):
        try:
            return session.query(table_class).filter(pk == id).one()
        except NoResultFound:
            abort(requests.codes.not_found)

    def get(self, id=None):
        if id:
            objs = [get_object(id)]
        else:
            objs = session.query(table_class).all()
        return {table_class.__name__: [serialize(_) for _ in objs]}

    def post(self):
        objs = [table_class(**_) for _ in request.json]
        for _ in objs:
            session.add(_)
        session.commit()
        return {table_class.__name__: [serialize(_) for _ in objs]}

    def put(self):
        obj = get_object(request.json[pk.name])
        for k, v in request.json.items():
            if k != pk.name:
                setattr(obj, k, v)
        session.commit()
        return {table_class.__name__: [serialize(obj)]}

    def delete(self, id):
        obj = get_object(id)
        session.delete(obj)
        session.commit()
        return {table_class.__name__: [serialize(obj)]}

    return type(
        table_class.__name__ + 'Resource',
        (Resource,),
        {
            'get': get,
            'post': post,
            'put': put,
            'delete': delete,
        })


for table_class in table_classes:
    resource_class = make_table_resource_class(table_class)
    api.add_resource(resource_class,
                     '/{}'.format(table_class.__name__),
                     '/{}/<id>'.format(table_class.__name__),
                     )


@api.representation('text/csv')
def output_csv(data, code, headers=None):
    buf = io.StringIO()
    for resource, rows in data.items():
        keys = sorted(list(rows[0].keys()))
        print(*keys, sep=',', file=buf)
        for row in rows:
            values = [row[_] for _ in keys]
            print(*values, sep=',', file=buf)

    resp = make_response(buf.getvalue(), code)
    resp.headers.extend(headers or {})
    return resp


if __name__ == '__main__':
    app.run(debug=True)
