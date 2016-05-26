from __future__ import print_function # In python 2.7
import json
import requests
import sys
import os

from flask import (render_template, url_for, redirect, request, 
    jsonify, flash, g, Markup, send_from_directory)
from flask_restful import Resource
from flask.ext.login import (login_user, logout_user, current_user,
    login_required)

from werkzeug import secure_filename
from werkzeug.security import (generate_password_hash,
     check_password_hash)

from . import url as orl
from . import app, db, upload_folder, es
from .forms import AddFile, SearchForm, SignInForm, SignUpForm
from .models import Users

import tika
from tika import parser

@app.before_request
def before_request():
    g.user = current_user


def types(extension):
    """
    Check of the file extension to allow the upload of the desired ones
    :param extension: The string of the aplication/type recieve
    :returns: The allowed :endpoint: in UPPERCASE :if: allowed

    """
    allowed = ['pdf', 'text']

    for endpoint in allowed:
        if endpoint in extension:
            return endpoint.upper()

    raise KeyError('File not allowed')


class Doc(Resource):
    """
    Class bound with the method :get: to retrieve an specific Doc
    """
    def get(self, doc_id):
        """
        Method designed to retrive an specific Doc without searchin the while node
        :param doc_id: The file id to get
        :returns: dictionary
        """
        url = orl.es_base_url['file']+ g.user.email + '/' + doc_id
        resp = requests.get(url)
        data = resp.json()
        doc = data['_source']
        doc['id'] = data['_id']
        return doc


class DocList(Resource):
    """
    Class bound with the method :func:`get` to retrieve all the Docs from one user
    """
    def get(self):
        """
        Method designed to retrieve all the Docs from the node of an specific user
        :retuns: list of dictionaries
        """
        url = orl.es_base_url['file']+ g.user.email + '/_search'
        query = {
            "query": {
                "match_all": {}
            },
            "size": 100
        }
        resp = requests.post(url, data=json.dumps(query))
        data = resp.json()
        docs = []

        for hit in data['hits']['hits']:
            doc = hit['_source']
            doc['id'] = hit['_id']
            docs.append(doc)
        return docs


class Search(Resource):
    """
    Class bound with the method to search in the entire node of a user
    for an specific doc
    """
 
    def get(self, field):
        """
        Search the node for a match, highligh the result if needed
        :paramr field: string to be match against the nodes
        :returns: list of dictionaries
        """
        url = orl.es_base_url['file']+ g.user.email + '/_search'
        query = {
            "query": {
                "multi_match": {
                    "fields": ["_id", "title", "body", "creator",
                        "file_name", "note", "file_type"],
                    "query": field,
                    "type": "phrase_prefix",
                    "use_dis_max": False
                }
            },
            "highlight": {
                    "pre_tags" : ["<em class='highlight'>"],
                    "post_tags" : ["</em>"],
                "fields" : {
                    "body": {"type": "plain", "fragment_size" : 45, "number_of_fragments" : 3},
                    "file_name": {"type": "plain", "fragment_size" : 30, "number_of_fragments" : 0},
                },
            "size": 100
        }
        }
        resp = requests.post(url, data=json.dumps(query))
        data = resp.json()
        docs = []

        for hit in data['hits']['hits']:
            doc = hit['_source']
            doc['id'] = hit['_id']

            try:
                highlight = hit['highlight']
            except KeyError:
                pass
            else:
                try:
                    doc['highlight'] = highlight['body']
                except KeyError:
                    doc['highlight'] = highlight['file_name']
            docs.append(doc)

        return docs

@app.route('/')
@app.route('/index', methods=['POST', 'GET'])
def index():
    value = request.form.get('doc')

    if value:
        if g.user.is_authenticated:
            results = Search().get(value)

            if results:
                return redirect(url_for('list', results=value))

            else:
                flash('No match found.')

        else:
            return redirect(url_for('non_search'))

    return render_template('index.html')


@app.route('/upload', methods=['POST', 'GET'])
def upload():
    """
    Uploads a file for to the user's folder and creates the 
    new index for the user in the Elasticsearc Node
    """
    form = AddFile()

    if form.validate_on_submit():
        try:
            file = form.file.data
            filename = secure_filename(file.filename)
            folder = os.path.join(upload_folder, g.user.email, filename)
            file.save(folder)
            parsed = parser.from_file(folder)

            try:
                parsed['metadata']['creator']
            except KeyError:
                parsed['metadata']['creator'] = None

            if not Search().get(filename):
                es.index(index='files', doc_type=g.user.email, body={
                    "title": form.title.data,
                    "file_type": types(parsed["metadata"]["Content-Type"]),
                    "creator": parsed["metadata"]["creator"],
                    "created": parsed["metadata"]["Creation-Date"],
                    "file_name": parsed["metadata"]["resourceName"],
                    "note": form.note.data,
                    "body": parsed["content"],
                })
            flash('Upload success')
            return redirect(url_for('index'))

        except KeyError as error:
            os.remove(folder)
            flash('File not allowed')
            return redirect('/upload')

    return render_template('upload.html', form=form)


@app.route('/list', methods=['POST', 'GET'])
def list():
    """
    Search for the list of possible results.
    If just one match is found then directly shows it
    """
    results = request.args['results']
    found = Search().get(results)

    if len(found) == 1:
        return redirect(url_for('show', results=found[0]['id']))

    else:
        return render_template('list.html', found=found)


@app.route('/show', methods=['POST', 'GET'])
def show():
    results = request.args['results']
    return render_template('show.html', file=Doc().get(results))


@app.route('/delete', methods=['POST', 'GET'])
def delete():
    """
    Deletes an index and the corresponding file in the user index and folder
    respectively
    """
    file_id = request.args['id']
    file = Doc().get(file_id)
    es.delete(index='files', doc_type=g.user.email, id=file_id)
    os.remove(os.path.join(upload_folder, g.user.email, file['file_name']))
    flash('Delete success.')
    return redirect(url_for('index'))


@app.route('/all_docs')
def all_docs():
    """
    :retuns: All the users documents
    """
    docs = DocList().get()
    return render_template('all_docs.html', docs=docs)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if g.user.is_authenticated:
        return redirect(url_for('index'))

    form = SignUpForm()

    if form.validate_on_submit():
        email = form.email.data
        u = Users(email=email, nickname=form.username.data,
            password=generate_password_hash(form.password.data))
        db.session.add(u)
        db.session.commit()

        if not os.path.exists(os.path.join(upload_folder, email)):
            os.makedirs(os.path.join(upload_folder, email))

        return redirect(url_for('signin'))

    return render_template('signup.html', form=form)


@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if g.user.is_authenticated:
        return redirect(url_for('index'))

    form = SignInForm()

    if form.validate_on_submit():
        u = Users.query.filter_by(email=form.email.data).first()
        
        if not u:
            return redirect(url_for('signin'))

        elif check_password_hash(u.password, form.password.data):
            login_user(u)
            return redirect(url_for('index'))

    return render_template('signin.html', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/non_search')
def non_search():
    """
    Function created for user non authentificated wich try to do a search
    """
    return render_template('non_search.html')


@app.route('/download', methods=['POST', 'GET'])
def download():
    file_id = request.args['id']
    file = Doc().get(file_id)
    folder = os.path.join(upload_folder, g.user.email)
    return send_from_directory(directory=folder, filename=file['file_name'])