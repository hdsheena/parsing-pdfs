from __future__ import division

import math
import pdfminer
from collections import defaultdict
import itertools

from pdfminer.high_level import extract_pages,extract_text,extract_text_to_fp

from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter

from pdfminer.layout import LAParams
from pdfminer.converter import PDFPageAggregator

import matplotlib.pyplot as plt
from matplotlib import patches

TEXT_ELEMENTS = [
    pdfminer.layout.LTTextBox,
    pdfminer.layout.LTTextBoxHorizontal,
    pdfminer.layout.LTTextLine,
    pdfminer.layout.LTTextLineHorizontal
]


def extract_layout_by_page(pdf_path):
    """
    Extracts the layouts of the pages of a PDF document
    specified by pdf_path.

    Uses the PDFminer library. See its documentation for
    details of the objects returned.

    See:
    - https://euske.github.io/pdfminer/programming.html
    - http://denis.papathanasiou.org/posts/2010.08.04.post.html
    """
    laparams = LAParams()

    fp = open(pdf_path, 'rb')
    parser = PDFParser(fp)
    document = PDFDocument(parser)

    if not document.is_extractable:
        raise PDFTextExtractionNotAllowed

    rsrcmgr = PDFResourceManager()
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)

    layouts = []
    for page in PDFPage.create_pages(document):
        interpreter.process_page(page)
        layouts.append(device.get_result())

    return layouts


def get_tables(pdf_path):
    """
    Tried to extract tabular information from the document in pdf_path.
    :param pdf_path: pdf document path
    :return: List of pages, each page is a list of lists
    """
    return [page_to_table(page_layout) for page_layout in
            extract_layout_by_page(pdf_path)]

def pairify(it):
    """find pairs of nearby numbers"""
    it0, it1 = itertools.tee(it, 2)
    first = next(it0)
    return zip(itertools.chain([first, first], it0), it1)

def cluster(sequence, maxgap):
    """get batches of similar numbers"""
    batch = []
    for prev, val in pairify(sequence):
        if val - prev >= maxgap:
            yield batch
            batch = []
        else:
            batch.append(val)
    if batch:
        yield batch

def page_to_table(page_layout):
    """
    Given a pdfminer page object, tries to convert it to a table
    :param page_layout
    :return: list of lists
    """
    texts = []
    rects = []
    other = []

    for e in page_layout:
        if isinstance(e, pdfminer.layout.LTTextBoxHorizontal):
            texts.append(e)
        elif isinstance(e, pdfminer.layout.LTRect):
            rects.append(e)
        else:
            other.append(e)

    # convert text elements to characters

    characters = extract_characters(texts)
    # get some rows to use for classifying characters
    box_char_dict_2 = {}
    last_char_right_bound = 0
    rows = []
    for c in characters:
        l_y =  c.bbox[1]
        rows.append(l_y)

    rows = sorted(rows)
    
    uniquerows1 = {}
    for row in cluster(rows,1):
        print(row[0])
        for num in row:
            uniquerows1[num]=row[0]
      
    for c in characters:
        # choose the row closest to this char's y coordinates:

        l_x, l_y = c.bbox[0], c.bbox[1]
        l_y_rounded = uniquerows1[l_y]
        #print(l_y_rounded)
        if l_y_rounded in box_char_dict_2.keys():
            box_char_dict_2[l_y_rounded].append(c)
            #continue
        else:
            box_char_dict_2[l_y_rounded] = [c]
            continue


        last_char_right_bound = c.bbox[2]
        

    return boxes_to_table_2(box_char_dict_2,uniquerows1)


def flatten(lst):
    """
    Flatterns a list of lists one level.
    :param lst: list of lists
    :return: list
    """
    return [subelem for elem in lst for subelem in elem]


def extract_characters(element):
    if isinstance(element, pdfminer.layout.LTChar):
        return [element]

    if any(isinstance(element, i) for i in TEXT_ELEMENTS):
        elements = []
        for e in element:
            elements += extract_characters(e)
        return elements

    if isinstance(element, list):
        return flatten([extract_characters(l) for l in element])

    return []





def chars_to_string_2(chars,uniquerows1):
    if not chars:
        return ""
    rows = sorted(list(set(uniquerows1[c.bbox[1]] for c in chars)), reverse=True)
    text = []
    text_so_far = ""
    last_char_right_bound = 0 
    y_position = 0
    # get a new string appended to the text list wherever the right edge of the previous character box is more than 1 pixel from the left edge of the current character box (ie: put words together)
    for row in rows:
        print("New row")
        sorted_row = sorted([c for c in chars if uniquerows1[c.bbox[1]] == row], key=lambda c: c.bbox[0])
        for c in sorted_row:
            #print(c.get_text())
            
            if c.bbox[0] - last_char_right_bound > 1:
                #print("new group of characters")
                text.append(text_so_far)
                text_so_far=""
            text_so_far+=c.get_text()
            last_char_right_bound = c.bbox[2]
            y_position = c.bbox[1]
    text.append(text_so_far)
    print(text)
    print("number of rows",len(rows))
    return text

def boxes_to_table_2(box_record_dict,uniquerows1):
    boxes = box_record_dict.keys()

    rows = sorted(list(set(b for b in boxes)), reverse=True)
    print(len(rows))
    table = []
    for row in rows:
        sorted_row = sorted([b for b in boxes if b == row], key=lambda b: b)
        for b in sorted_row:
            textToAppend = chars_to_string_2(box_record_dict[b],uniquerows1)
            table.append(textToAppend)
       
    return table

