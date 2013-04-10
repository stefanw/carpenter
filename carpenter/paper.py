import StringIO

from .ruler import Point


class Cell(object):
    image = None
    text = ''

    def __init__(self, top, right, bottom, left, **kwargs):
        self.top = top
        self.right = right
        self.bottom = bottom
        self.left = left

        if kwargs.get('colspan', 1) == 1:
            kwargs.pop('colspan')
        if kwargs.get('rowspan', 1) == 1:
            kwargs.pop('rowspan')
        self.kwargs = kwargs
        self.filename = self.kwargs['id'] + '.png'

    def to_html(self):
        attrs = dict((k, v) for k, v in self.kwargs.items())
        if self.image is not None:
            attrs['style'] = 'background-image:url(%s);width:%spx;height:%spx' % (
                self.filename,
                self.width,
                self.height
            )
        attrs['title'] = self.get_id()
        attrs = ' '.join(['%s="%s"' % (k, v) for k, v in attrs.items()])
        return '<td %s>%s</td>' % (attrs, self.text)

    @property
    def width(self):
        return int(self.right.a.x) - int(self.left.a.x)

    @property
    def height(self):
        return int(self.bottom.a.y) - int(self.top.a.y)

    def get_id(self):
        return self.kwargs['id']

    def as_dict(self):
        d = dict(self.kwargs)
        d.update({
            'text': self.text,
            'width': self.width,
            'height': self.height
        })
        return d


class Table(object):
    def __init__(self, table_id, row_count, col_count):
        self.id = table_id
        self.row_count = row_count
        self.col_count = col_count
        self.cells = []
        self.row_index = -1
        self.col_index = -1
        for i in range(row_count):
            self.cells.append([None for j in range(col_count)])

    def prepare_cell(self):
        self.col_index += 1
        if self.col_index > self.col_count - 1 or self.col_index == 0:
            self.row_index += 1
            self.col_index = 0
        if self.row_index > self.row_count - 1:
            raise IndexError
        if self.cells[self.row_index][self.col_index] is False:
            return False
        return True

    def add_cell(self, top_line, right_line, bottom_line, left_line,
                 colspan=1, rowspan=1):
        # print "add_cell", colspan, rowspan, self.row_index, self.row_count
        for i in range(rowspan):
            for j in range(colspan):
                self.cells[self.row_index + i][self.col_index + j] = False
        cell = Cell(top_line, right_line, bottom_line, left_line,
                colspan=colspan, rowspan=rowspan,
                id='cell-%d-%d-%d' % (self.id, self.row_index, self.col_index))
        self.cells[self.row_index][self.col_index] = cell

    def get_cells(self):
        for i in range(self.row_count):
            for j in range(self.col_count):
                if self.cells[i][j]:
                    yield self.cells[i][j]

    def to_html(self):
        out = StringIO.StringIO()
        out.write('<table id="%s">\n' % self.id)
        for i in range(self.row_count):
            out.write(' <tr>\n')
            for j in range(self.col_count):
                # print self.cells[i][j]
                if self.cells[i][j]:
                    out.write('  %s\n' % self.cells[i][j].to_html())
            out.write(' </tr>\n')
        return out.getvalue()

    def as_dict(self):
        return {
            'cells': self.cells,
            'row_count': self.row_count,
            'col_count': self.col_count,
            'id': self.id
        }


class Paper(object):
    def __init__(self):
        self.tables = []

    def get_colspan(self, hl, coming_vls, last_hl_y):
        midpoint = Point(0, (hl.a.y + last_hl_y) / 2)
        colspan = 1
        for cvl in coming_vls:
            if not cvl.contains(midpoint):
                colspan += 1
            else:
                return colspan, cvl
        return colspan, None

    def get_rowspan(self, vl, coming_hls, last_vl_x):
        midpoint = Point((vl.a.x + last_vl_x) / 2, 0)
        rowspan = 1
        for chl in coming_hls:
            # print chl, len(coming_hl), mid
            if not chl.contains(midpoint):
                rowspan += 1
            else:
                return rowspan, chl
        return rowspan, None

    def sketch(self, lines):
        v_lines = filter(lambda x: not x.is_horizontal, lines)
        v_lines.sort(key=lambda x: x.top())
        h_lines = filter(lambda x: x.is_horizontal, lines)
        h_lines.sort(key=lambda x: x.top())

        while v_lines:
            v_line = v_lines[0].clone()

            nv_lines = []
            cv_lines = []
            # Find first table (vertical line area)
            # store in cv_lines
            for vl in v_lines:
                if v_line.overlap(vl):
                    v_line.merge(vl)
                    cv_lines.append(vl)
                else:
                    nv_lines.append(vl)
            v_lines = nv_lines
            cv_lines.sort(key=lambda x: x.left())

            # Find all horizontal lines
            # in that table
            ch_lines = []
            for hl in h_lines:
                if v_line.overlap(hl):
                    ch_lines.append(hl)

            table = Table(
                table_id=len(self.tables),
                col_count=len(cv_lines) - 1,
                row_count=len(ch_lines) - 1
            )
            self.tables.append(table)

            last_hl_y = ch_lines[0].a.y

            ch_lines.sort(key=lambda x: x.top())
            for i, hl in enumerate(ch_lines):
                if i == 0:
                    continue
                last_vl_x = cv_lines[0].a.x
                for j, vl in enumerate(cv_lines):
                    if j == 0:
                        continue
                    if table.prepare_cell():
                        # Find the span of this cell
                        colspan, right_line = self.get_colspan(hl, cv_lines[j:], last_hl_y)
                        rowspan, bottom_line = self.get_rowspan(vl, ch_lines[i:], last_vl_x)
                        table.add_cell(
                            ch_lines[i - 1],
                            right_line,
                            bottom_line,
                            cv_lines[j - 1],
                            colspan=colspan,
                            rowspan=rowspan
                        )
                    last_vl_x = vl.a.x
                last_hl_y = hl.a.y
