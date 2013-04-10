import subprocess
import os

from lxml import etree


class Bench(object):
    def __init__(self, filename=None, pdftohtml='pdftohtml',
                make_thumbnail='convert -density 300 -depth 8 -quality 85'):
        self.filename = filename
        self.pdftohtml = pdftohtml
        self.make_thumbnail = make_thumbnail

    def get_meta(self, filename=None):
        if filename is None:
            filename = self.filename

        p = subprocess.Popen(['pdfinfo', filename],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        out, err = p.communicate()
        lines = out.splitlines()
        meta = {}
        for line in lines:
            if not line:
                continue
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            meta[key] = value
        return meta

    def generate_images(self, pages, sizes=['', 'x300']):
        base, ext = self.filename.rsplit('.', 1)
        for size in sizes:
            size = str(size)
            for i, page in enumerate(pages):
                params = self.make_thumbnail.split(' ')
                if size:
                    params.extend(['-thumbnail', size])
                params.append('%s[%d]' % (self.filename, i))
                nsize = size
                if size:
                    nsize = '-' + size
                out = '%s-%d%s.png' % (base, i, nsize)
                params.append(out)
                page.setdefault('thumbnails', {})
                page['thumbnails'][size] = out
                p = subprocess.Popen(params,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)
                out, err = p.communicate()

    def get_xml_file(self, filename, out):
        base = os.path.basename(filename).rsplit('.')[0]
        xml_file_path = os.path.join(out, base + '.xml')
        params = [self.pdftohtml, '-xml',
            '-s', filename, xml_file_path]
        p = subprocess.Popen(params, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        out, err = p.communicate()
        return file(xml_file_path)

    def get_pages(self, xml_file):
        root = etree.fromstring(xml_file.read())
        pages = []
        for i, page in enumerate(root.xpath("//page")):
            images = []
            for image in page.xpath('./image'):
                images.append({
                    'top': int(image.attrib['top']),
                    'left': int(image.attrib['left']),
                    'width': int(image.attrib['width']),
                    'height': int(image.attrib['height']),
                    'src': image.attrib['src']
                })
            pages.append({'images': images})
        return pages

    def setup(self, out):
        xml_file = self.get_xml_file(self.filename, out)
        pages = self.get_pages(xml_file)
        return pages
        # images = self.get_images(self.filename)
