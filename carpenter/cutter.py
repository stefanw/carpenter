import cv2
import sys
import os
import math

from .ruler import Ruler, is_horizontal, is_vertical


class Cutter(object):
    def __init__(self, filename, threshold=(0, 0, 0, 0)):
        self.path = os.path.dirname(filename)
        self.img = cv2.imread(filename)
        self.threshold = threshold

    def cutoff_remains(self, x1, y1, x2, y2):
        # cutoff left with middle sample check
        i = 0
        BORDER = int(math.floor((y2 - y1) * 0.05))
        sl1, sl2 = y1 + BORDER, y2 - BORDER
        img = self.img[sl1:sl2, x1:x2]
        col_value = lambda i: sum([sum(img[:, i, 0]),
            sum(img[:, i + 1, 0])
        ])
        while col_value(i) / (2 * 255.0) / (sl2 - sl1) < 0.9 and i < 15:
            i += 1
        x1 += i

        # cutoff right with middle sample check
        i = 1
        col_value = lambda i: sum([sum(img[:, -i, 0]),
            sum(img[:, -(i + 1), 0])
        ])
        while col_value(i) / (2 * 255.0) / (sl2 - sl1) < 0.9 and i < 15:
            i += 1
        x2 -= (i - 1)

        # cutoff top with middle sample check
        i = 0
        img = self.img[y1:y2, x1:x2]
        row_value = lambda i: sum([sum(img[i, :, 0]),
            sum(img[i + 1, :, 0])
        ])
        while row_value(i) / (2 * 255.0) / (x2 - x1) < 0.9 and i < 15:
            i += 1
        y1 += i

        # cutoff bottom with middle sample check
        i = 1
        row_value = lambda i: sum([sum(img[-i, :, 0]),
            sum(img[-(i + 1), :, 0])
        ])
        while row_value(i) / (2 * 255.0) / (x2 - x1) < 0.9 and i < 15:
            i += 1
        y2 -= (i - 1)

        return x1, y1, x2, y2

    def find_contours(self, img):
        imgray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        contours, hierarchy = cv2.findContours(imgray, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(img, contours, -1, (0, 255, 0), 1)
        return img

    def cleanup(self, img):
        new_contours = []
        height, width, _ = img.shape
        # max_area = width * height * 0.0005
        imgray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        contours, hierarchy = cv2.findContours(imgray, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 20:
                new_contours.append(contour)

        cv2.drawContours(imgray, contours, -1, (255, 255, 255), -1)
        return imgray

    def cutoff(self, img, x1, y1, x2, y2, padding=3):
        width, height = x2 - x1, y2 - y1
        margin = width * 0.1, height * 0.1
        ruler = Ruler(image=img)
        lines = ruler.get_bordered_lines(
            # maxLineGap=6,
            # minLineLength=min(width * 0.4, height * 0.4)
        )
        ax1, ax2, ay1, ay2 = 0, width, 0, height
        for line in lines:
            cv2.line(img, line.a, line.b, (0, 0, 255), 1)
            if is_horizontal(line):
                if line.a.y < margin[1]:
                    ay1 = max(line.a.y + padding, ay1)
                elif line.a.y > height - margin[1]:
                    ay2 = min(line.a.y - padding, ay2)
            elif is_vertical(line):
                if line.a.x < margin[0]:
                    ax1 = max(line.a.x + padding, ax1)
                elif line.a.x > width - margin[0]:
                    ax2 = min(line.a.x - padding, ax2)
        return x1 + ax1, y1 + ay1, x2 - (width - ax2), y2 - (height - ay2)

    def cut_cell(self, cell):
        """
        All of the following made OCR worse
        - manually detecting edges and cutting them off
        - finding contours, cutting them off
        - finding edges again, cutting them off
        x1, y1, x2, y2 = self.cutoff_remains(x1, y1, x2, y2)
        x1, y1, x2, y2 = self.cutoff(self.img[y1:y2, x1:x2], x1, y1, x2, y2)
        print x1, y1, x2, y2
        cell.image = self.find_contours(self.img[y1:y2, x1:x2])
        Looks like leaving a healthy margin is best
        """
        self.threshold = (-5, -5, -5, -5)
        x1 = cell.left.a.x + self.threshold[0]
        y1 = cell.top.a.y + self.threshold[3]
        x2 = cell.right.a.x - self.threshold[1]
        y2 = cell.bottom.a.y - self.threshold[2]

        # cell.image = self.cleanup(self.img[y1:y2, x1:x2])
        cell.image = self.img[y1:y2, x1:x2]
        cell.filename = os.path.join(self.path, cell.filename)
        cv2.imwrite(cell.filename, cell.image)

    def cut_table(self, table):
        for cell in table.get_cells():
            self.cut_cell(cell)

    def cut(self, tables):
        for table in tables:
            self.cut_table(table)
