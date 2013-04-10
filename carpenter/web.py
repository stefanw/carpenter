import os
import json
from datetime import datetime

from flask import Flask, request, g, redirect, url_for, abort, render_template
from werkzeug import secure_filename

import dataset

from .utils import mkdir_p, JSONEncoder
from .tasks import analyze_file, analyze_image
from . import default_settings


app = Flask('carpenter')
app.config.from_object(default_settings)
app.config.from_envvar('CARPENTER_SETTINGS', silent=True)


def connect_db():
    return dataset.connect('sqlite:///carpenter.db')


@app.before_request
def before_request():
    g.db = connect_db()


@app.route('/project/create', methods=['POST'])
def project_create():
    name = request.form['name']
    g.db['project'].upsert(dict(name=name, created=datetime.utcnow()), ['name'])
    project = g.db['project'].find_one(name=name)
    return redirect(url_for('project', project_id=project['id']))


@app.route('/project/upload', methods=['POST'])
def project_upload():
    project_id = int(request.form['project_id'])
    project = g.db['project'].find_one(id=project_id)
    name = request.form['name']
    description = request.form['description']
    f = request.files['file']
    name = name or f.filename
    secure_name = secure_filename(f.filename)
    data = dict(
        project=project_id,
        path='',
        filename=secure_name,
        name=name,
        status='analyzing',
        description=description,
        created=datetime.utcnow()
    )
    g.db['file'].upsert(data, ['filename'])
    file_dict = g.db['file'].find_one(filename=secure_name, project=project_id)
    ext = secure_name.rsplit('.', 1)[1]
    filename = '%s.%s' % (file_dict['id'], ext)
    path = os.path.join(app.config['MEDIA_PATH'], str(project['id']), str(file_dict['id']))
    mkdir_p(path)
    path = os.path.join(path, filename)
    f.save(path)
    path = path.rsplit('/static/', 1)[1]
    file_dict['path'] = path
    g.db['file'].update(file_dict, ['id'])
    analyze_file.delay(file_dict['id'])
    return redirect(url_for('project', project_id=str(project['id'])))


@app.route('/project/<project_id>/')
def project(project_id):
    project = g.db['project'].find_one(id=int(project_id))
    if not project:
        abort(404)
    files = list(g.db['file'].find(project=int(project_id)))
    for f in files:
        file_pages = list(g.db['page'].find(file=int(f['id'])))
        for p in file_pages:
            page_images = list(g.db['image'].find(page=int(p['id'])))
            for i in page_images:
                tables = list(g.db['table'].find(image=int(i['id'])))
                i['tables'] = tables
            p['images'] = page_images
        f['pages'] = file_pages
    project['files'] = files
    project_json = json.dumps(project, cls=JSONEncoder)
    return render_template('project.html',
        project=project,
        project_json=project_json)


@app.route('/project/<project_id>/image/<image_id>/analyze', methods=['POST'])
def image_analyze(project_id, image_id):
    project = g.db['project'].find_one(id=int(project_id))
    if not project:
        abort(404)
    image = g.db['image'].find_one(id=int(image_id))
    if not image:
        abort(404)
    res = analyze_image.delay(image['id'])
    return json.dumps({'ref': res.id})


@app.route('/')
def index():
    projects = g.db['project'].all()
    return render_template('index.html', projects=projects)


if __name__ == '__main__':
    app.run()
