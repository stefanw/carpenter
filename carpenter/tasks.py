import json
import os

from celery import Celery

from . import Bench, Ruler, Paper, Cutter, Plane
from .utils import JSONEncoder

celery = Celery('carpenter')


def update_status(table, obj, status):
    obj['status'] = status
    table.update(obj, ['id'])


def make_relative(filename):
    if filename:
        return filename.rsplit('/static/', 1)[1]
    return ''


@celery.task
def analyze_file(file_id):
    from .web import connect_db
    from .web import app
    db = connect_db()

    file_dict = db['file'].find_one(id=file_id)

    filename = os.path.join(app.config['STATIC_PATH'], file_dict['path'])
    basepath = os.path.dirname(filename)
    bench = Bench(filename)

    ext = file_dict['path'].rsplit('.')[1]
    if ext == 'pdf':
        meta = bench.get_meta(file_dict['path'])
        update_status(db['file'], file_dict, 'Extracting PDF...')
        pages = bench.setup(basepath)
    else:
        pages = [{'images': [{'src': file_dict['path']}]}]
        meta = {}
    update_status(db['file'], file_dict, 'Generate Thumbnails...')
    bench.generate_images(pages, sizes=['', 'x300'])
    update_status(db['file'], file_dict, 'Storing results...')
    file_dict['meta'] = json.dumps(meta)
    file_dict['page_count'] = meta.get('Page', 1)
    for i, page in enumerate(pages):
        data = {
            'file': file_dict['id'],
            'number': i,
            'thumbnail': make_relative(page['thumbnails'].get('x300')),
            'image': make_relative(page['thumbnails'].get(''))
        }
        print data
        print db['page'].upsert(data, ['file', 'number'])
        page_obj = db['page'].find_one(file=data['file'], number=data['number'])
        for j, image in enumerate(page['images']):
            src = make_relative(image.get('src'))
            db['image'].upsert({
                'page': page_obj['id'],
                'file': file_dict['id'],
                'number': j,
                'top': image.get('top'),
                'left': image.get('left'),
                'width': image.get('width'),
                'height': image.get('height'),
                'path': src,
            }, ['page', 'number'])
    update_status(db['file'], file_dict, 'done')
    print file_id, file_dict


@celery.task
def analyze_image(image_id):
    from .web import connect_db
    from .web import app
    db = connect_db()

    image = db['image'].find_one(id=image_id)

    filename = os.path.join(app.config['STATIC_PATH'], image['path'])

    ruler = Ruler(filename)
    ruler.apply()
    ruler.draw()
    paper = Paper()
    paper.sketch(ruler.lines)
    cutter = Cutter(filename)
    cutter.cut(paper.tables)
    plane = Plane(lang='deu', auto_numbers=True)
    plane.use(paper.tables)
    for i, table in enumerate(paper.tables):
        db['table'].upsert({
            'number': i,
            'row_count': table.row_count,
            'col_count': table.col_count,
            'table_id': table.id,
            'image': image['id'],
            'data': json.dumps(table.cells, cls=JSONEncoder)
        }, ['image', 'table_id'])
