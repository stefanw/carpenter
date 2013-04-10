# Carpenter

## Creates tables out of images

Carpenter takes images that contain tables as pixels and tries to convert them to HTML tables (e.g. HTML tables).

If you need to extract tables out of text PDFs, have a look at [Tabula](https://github.com/jazzido/tabula).


### Installation

You need OpenCV and the OpenCV python bindings. On OS X a `brew install opencv` installs OpenCV, but you have to make the Python library available (look at the last lines of brew's output). Copying the cv*.(so|py) to you virtual env's site-packages folder is enough.

### Carpenter Make Tables (Command line)

    python make_tables.py [options] imagefile.png > output.html


### Carpenter Workshop (Web Interface)

The Carpenter Workshop has the goal to make it easy to extract the same kinds of tables out of multiple PDF files by detecting table layouts and applying predefined extraction steps. It's not yet there, though.

It requires libpoppler with the pdftohtml/pdfimages commands and ImageMagick with convert. You also have to install the web dependencies with

    pip install -r pip-requirements.txt

Start the workshop with

    python open_workshop.py

Also run the Carpenter task worker with a Celery worker queue of your choosing:

    rabbitmq-server &
    celeryd -l INFO -I carpenter.tasks

Workshop configuration's defaults are in `carpenter.default_settings` and can be overridden with something like

    export CARPENTER_SETTINGS=my_settings.cfg


### Carpenter Tools (Python library)

There are a couple of modules inside carpenter that can be used more or less independently to accomplish some carpentry tasks:

- `carpenter.bench`: Takes a PDF file and extracts pages and images
- `carpenter.ruler`: Detects horizontal and vertical lines in an image
- `carpenter.paper`: Takes horizontal and vertical lines and creates a table structure out of them
- `carpenter.cutter`: Cuts table cells out of images
- `carpenter.plane`: Runs OCR on extracted table cell images

For usage see `make_tables.py`, `carpenter.tasks` and the code itself.
