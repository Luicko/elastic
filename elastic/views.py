from __future__ import print_function # In python 2.7
import json
import requests
import sys
import os

from flask import render_template, url_for, redirect, request, jsonify, flash
from flask_restful import Resource
from flask.ext.login import current_user
from werkzeug import secure_filename

from . import url as orl
from . import app, db, api, parsor, UPLOAD_FOLDER
from .forms import AddFile, SearchForm

import tika
from tika import parser
from elasticsearch import Elasticsearch


class Search(Resource):
 
    def get(self, field):
        url = orl.es_base_url['doc']+'/_search'
        query = {
            "query": {
                "multi_match": {
                    "fields": ["_id", "title", "body", "creator", "note", "file_type"],
                    "query": field,
                    "type": "phrase_prefix",
                    "use_dis_max": False
                }
            },
            "size": 100
        }
        resp = requests.post(url, data=json.dumps(query))
        data = resp.json()
        peoples = []
        for hit in data['hits']['hits']:
            people = hit['_source']
            people['id'] = hit['_id']
            peoples.append(people)
        return peoples

@app.route('/')
@app.route('/index')
def index():
    print(UPLOAD_FOLDER, file=sys.stderr)
    return render_template('index.html')

@app.route('/upload', methods=['POST', 'GET'])
def upload():
    form = AddFile()
    if form.validate_on_submit():
        es = Elasticsearch()
        parsed = parser.from_buffer(form.file.data)
        file = form.file.data
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        flash('Upload success')
        try:
            parsed['metadata']['creator']
        except KeyError:
            parsed['metadata']['creator'] = None
        es.index(index='files', doc_type='doc', body={
            "title": form.title.data,
            "file_type": parsed["metadata"]["Content-Type"],
            "creator": parsed["metadata"]["creator"],
            "created": parsed["metadata"]["Creation-Date"],
            "note": form.note.data,
            "body": parsed["content"],
        })
        return redirect(url_for('index'))
    return render_template('upload.html', form=form)

@app.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    if form.validate_on_submit():
        results = Search().get(form.field.data)
        if results:
            return redirect(url_for('list', results=form.field.data))
        else:
            flash('No match found.')
    return render_template('search.html', form=form)

@app.route('/list', methods=['POST', 'GET'])
def list():
    results = request.args['results']
    found = Search().get(results)
    if len(found) == 1:
        return redirect(url_for('show', results=results))
    else:
        return render_template('list.html', found=found)

@app.route('/show', methods=['POST', 'GET'])
def show():
    results = request.args['results']
    return render_template('show.html', file=Search().get(results)[0])

@app.route('/delete', methods=['POST', 'GET'])
def delete():
    thing = request.form.get('id')
    es = Elasticsearch()
    es.delete(index='files', doc_type='doc', id=thing)
    flash('Delete success.')
    return redirect(url_for('index'))