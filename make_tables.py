import sys
import os

from carpenter import Ruler, Paper, Cutter, Plane


TESSERACT_CONFIG_PATH = os.path.join(os.path.abspath(
        os.path.dirname(__file__)), 'etc', 'tesseract')


def make_tables(args, options):
    sys.stdout.write(
            '''<!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title></title>
      <style type="text/css" media="screen">
        table {
          table-layout: fixed;
        }
        table,tr, td {
          font-size: 18px;
          border: 1px solid #000;
        }
        td {
          background-repeat: no-repeat;
          background-position: -999999px 0px;
          background-size: 100% auto;
        }
        td:hover {
            background-position: 0px 0px;
        }
      </style>
    </head>
    <body>''')

    for filename in args:
        ruler = Ruler(filename)
        ruler.apply()
        ruler.draw()
        paper = Paper()
        paper.sketch(ruler.lines)
        cutter = Cutter(filename)
        cutter.cut(paper.tables)
        plane = Plane(
            config_path=TESSERACT_CONFIG_PATH,
            lang=options.language,
            auto_numbers=True
        )
        plane.use(paper.tables)

        for table in paper.tables:
            sys.stdout.write(table.to_html())

    sys.stdout.write('''</body></html>''')


if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser(usage='usage: %prog [options] [arg1...]\n'
                          'Carpenter makes tables from images')
    parser.add_option("-l", "--lang", default='eng',
                      action="store", type="string", dest="language",
                      help="Language to use for tesseract (e.g. eng, deu)")
    parser.add_option("--no-smart-numbers", default=True,
                      action="store_false", dest="smart_numbers",
                      help="Detect number in cell, reparse with tesseract numbers config")

    (options, args) = parser.parse_args()

    make_tables(args, options)
