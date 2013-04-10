# -*- encoding: utf-8 -*-
import sys
import math
import json
from itertools import chain
from collections import namedtuple

import cv2

Point = namedtuple('Point', ['x', 'y'])
Line = namedtuple('Line', ['a', 'b'])


def angle(p1, p2):
    xDiff = float(p2.x - p1.x)
    yDiff = float(p2.y - p1.y)
    return math.atan2(yDiff, xDiff) * (180 / math.pi)


def is_horizontal(line):
    return angle(line.a, line.b) % 180 < 2


def is_vertical(line):
    return (angle(line.a, line.b) + 90) % 180 < 2


def line_factory(line):
    if is_horizontal(line):
        return HorizontalLine(line)
    return VerticalLine(line)


class LineContainer(object):
    OVERLAP_THRESHOLD = 30
    DISTANCE_THRESHOLD = 20

    def __init__(self, line):
        self.a = line.a
        self.b = line.b
        # a should contain the greater point
        self.order_points()

    def __str__(self):
        return '%s%s%s' % (self.a, self.separator, self.b)

    def to_builtin(self):
        return [[int(self.a.x), int(self.a.y)],
                [int(self.b.x), int(self.b.y)],
                self.is_horizontal]

    def clone(self):
        return self.__class__(Line(self.a, self.b))

    def top(self):
        return self.b.y

    def left(self):
        return self.b.x


class HorizontalLine(LineContainer):
    separator = '-'
    is_horizontal = True
    OVERLAP_THRESHOLD = 150
    DISTANCE_THRESHOLD = 20

    def order_points(self):
        if self.a.x < self.b.x:
            self.a, self.b = self.b, self.a

    def contains(self, point, threshold=5):
        return self.a.x + threshold > point.x and self.b.x - threshold < point.x

    def overlap(self, line):
        return (self.a.x + self.OVERLAP_THRESHOLD > line.b.x and
                line.a.x + self.OVERLAP_THRESHOLD > self.b.x)

    def similar(self, line):
        return abs(self.a.y - line.a.y) < self.DISTANCE_THRESHOLD and self.overlap(line)

    def merge(self, line):
        ptmin = min(self.a.x, self.b.x, line.a.x, line.b.x)
        ptmax = max(self.a.x, self.b.x, line.a.x, line.b.x)
        avg = sum([self.a.y, self.b.y, line.a.y, line.b.y]) / 4
        self.a = Point(ptmax, avg)
        self.b = Point(ptmin, avg)


class VerticalLine(LineContainer):
    separator = '|'
    is_horizontal = False

    def order_points(self):
        if self.a.y < self.b.y:
            self.a, self.b = self.b, self.a

    def contains(self, point, threshold=5):
        return self.a.y + threshold > point.y and self.b.y - threshold < point.y

    def overlap(self, line):
        return (self.a.y + self.OVERLAP_THRESHOLD > line.b.y and
            line.a.y + self.OVERLAP_THRESHOLD > self.b.y)

    def similar(self, line):
        return abs(self.a.x - line.a.x) < self.DISTANCE_THRESHOLD and self.overlap(line)

    def merge(self, line):
        ptmin = min(self.a.y, self.b.y, line.a.y, line.b.y)
        ptmax = max(self.a.y, self.b.y, line.a.y, line.b.y)
        avg = sum([self.a.x, self.b.x, line.a.x, line.b.x]) / 4
        self.a = Point(avg, ptmax)
        self.b = Point(avg, ptmin)


class Ruler(object):
    strategies = {
        'bordered': 'get_bordered_lines'
    }

    def __init__(self, filename=None, image=None):
        if image is not None:
            self.img = image
        else:
            self.filename = filename
            self.img = cv2.imread(filename)

    def find_lines(self, image, rho=4, theta=math.pi,
            threshold=1, minLineLength=100, maxLineGap=3, **kwargs):
        """

        rho – Distance resolution of the accumulator in pixels.
        theta – Angle resolution of the accumulator in radians.
        threshold – Accumulator threshold parameter. Only those lines are returned that get enough votes (  ).
        minLineLength – Minimum line length. Line segments shorter than that are rejected.
        maxLineGap – Maximum allowed gap between points on the same line to link them.
        """

        lines = cv2.HoughLinesP(image, rho, theta, threshold,
                                None, minLineLength, maxLineGap)
        if lines[0] is not None:
            for line in lines[0]:
                yield Line(Point(line[0], line[1]), Point(line[2], line[3]))
                # if angle(pt1, pt2) % 90 == 0:

    def get_bordered_lines(self, **kwargs):
        # (mu, sigma) = cv2.meanStdDev(gray)
        # edges = cv2.Canny(gray, mu - sigma, mu + sigma)
        # edges = cv2.Canny(gray, 50, 150, 7)
        # cv2.imwrite("002-0e.png", edges)
        gray = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)
        gray = cv2.bitwise_not(gray)
        return chain.from_iterable([
            self.find_lines(gray, theta=math.pi / 2, **kwargs),
            self.find_lines(gray, theta=math.pi, **kwargs)
        ])

    def merge_lines(self, lines):
        current_len = len(lines)
        old_len = 0
        new_lines = []
        while current_len != old_len:
            old_len = current_len
            new_lines = []
            for line in lines:
                similar = False
                for nl in new_lines:
                    if line.similar(nl):
                        nl.merge(line)
                        similar = True
                        break
                if not similar:
                    new_lines.append(line)
            lines = new_lines
            current_len = len(lines)
        return new_lines

    def apply(self, strategy='bordered'):
        lines = []
        raw_lines = getattr(self, self.strategies[strategy])()

        for line in raw_lines:
            lines.append(line_factory(line))

        new_lines = []
        new_lines.extend(self.merge_lines(filter(lambda x: x.is_horizontal, lines)))
        new_lines.extend(self.merge_lines(filter(lambda x: not x.is_horizontal, lines)))
        self.lines = new_lines

        return new_lines

    def draw(self):
        for line in self.lines:
            cv2.line(self.img, line.a, line.b, (0, 0, 255), 3)
        filename = self.filename.rsplit('.', 1)
        filename[0] += '-lines'
        cv2.imwrite('.'.join(filename), self.img)


def main(args, options):
    for filename in args:
        lines = Ruler(filename).apply()
        if options.image:
            img = cv2.imread(filename)
            for line in lines:
                cv2.line(img, line.a, line.b, (0, 0, 255), 3)
            cv2.imwrite(options.image, img)
        sys.stdout.write(json.dumps([l.to_builtin() for l in lines]))
        sys.stdout.write('\n')

if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-i", "--image", dest="image",
                      help="write detected on image to file", metavar="FILE")

    (options, args) = parser.parse_args()

    main(args, options)
