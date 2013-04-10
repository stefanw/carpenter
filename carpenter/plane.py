import subprocess
import re
import sys
import os


class Plane(object):
    def __init__(self, **options):
        self.lang = options.get('lang', 'eng')
        self.config_path = options.get('config_path')
        self.config = options.get('config')
        self.smart_numbers = options.get('smart_numbers')

    def call_tesseract(self, cell, config=None):
        params = ["tesseract", cell.filename,
            cell.filename, '-l', self.lang, '-psm', '6']
        if config:
            params.append(config)
        p = subprocess.Popen(params, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        out, err = p.communicate()
        if p.returncode == 0:
            return file(cell.filename + '.txt').read()
        else:
            sys.stderr.write(err)

    def ocr_cell(self, cell):
        text = self.call_tesseract(cell, self.config)
        if self.smart_numbers and self.likely_number(text):
            number_config = os.path.join(self.config_path, 'numbers')
            text = self.call_tesseract(cell, number_config)
        cell.text = text

    def likely_number(self, text):
        text = text.strip()
        if not len(text):
            return False
        new_text = re.sub('[^\d.,+-]', '', text)
        return float(len(new_text)) / len(text) > 0.8

    def use_table(self, table):
        for cell in table.get_cells():
            self.ocr_cell(cell)

    def use(self, tables):
        for table in tables:
            self.use_table(table)
