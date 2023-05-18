from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.layout import LAParams
from pdfminer.converter import PDFPageAggregator
import pdfminer
import numpy as np
import cv2
import json
import os
import argparse

parser = argparse.ArgumentParser(description='Parse PDF files', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('-f', 
                    '--filename', 
                    help='pdf filename, without extension',
                    metavar='str',
                    type=str,
                    default='one')

args = parser.parse_args()

filename = args.filename
pdf_path = f'data/pdf_sample/{filename}.pdf' # pdf 파일 경로 지정
try:
    fp = open(pdf_path, 'rb') # pdf 파일 열기
except FileNotFoundError:
    print('File not found...')
    exit()
parser = PDFParser(fp) # pdf 파일과 관련된 parser생성
doc = PDFDocument(parser) # pdf 문서 구조를 저장하는 PDFDocument 겍체 생성

# pdf 내용 추출 가능 여부 판단
if not doc.is_extractable:
    raise PDFTextExtractionNotAllowed

rsrcmgr = PDFResourceManager() # 공유 자원을 저장하는 PDFResourceManager객체 생성
laparams = LAParams() # Layout 파라미터 객체생성
device = PDFPageAggregator(rsrcmgr, laparams=laparams) # PDFPageAggregator객체 생성
interpreter = PDFPageInterpreter(rsrcmgr, device) # PDFPageInterpreter객채 생성

pdf_data = {} # pdf 전체 데이터를 담을 dict

pdf_data['version'] = '1.0'
pdf_data['page_list'] = []

for page in PDFPage.create_pages(doc): # 페이지 별로 처리
    interpreter.process_page(page)
    layout = device.get_result() # layout 결과 가져오기

    print(f'#################### {layout.pageid}')

    page_data = {} # 해당 페이지의 데이터

    page_data['page_id'] = layout.pageid # 페이지 번호
    page_data['page_width'] = layout.bbox[2] - layout.bbox[0]  # 페이지 너비
    page_data['page_height'] = layout.bbox[3] - layout.bbox[1]  # 페이지 높이

    page_data['text_list'] = [] # 텍스트 정보 리스트

    for obj in layout._objs:
        if isinstance(obj, pdfminer.layout.LTTextBoxHorizontal):
            data_item = {}
            data_item['bbox'] = {}
            data_item['bbox']['x1'] = obj.bbox[0]
            data_item['bbox']['y1'] = layout.bbox[3] - obj.bbox[3]
            data_item['bbox']['x2'] = obj.bbox[2]
            data_item['bbox']['y2'] = layout.bbox[3] - obj.bbox[1]
            data_item['text'] = obj.get_text()
            page_data['text_list'].append(data_item)

    pdf_data['page_list'].append(page_data)

json_data = json.dumps(pdf_data)
print(json_data)

json_path = f'data/json_result/{filename}.json'
with open(json_path, 'w', encoding='UTF8') as json_file:
    json_file.write(json_data) # json데이터를 파일에 쓰기

colors = {'blue': (255, 0, 0), 'green': (0, 255, 0), 'red': (0, 0, 255), 'yellow': (0, 255, 255),
          'magenta': (255, 0, 255), 'cyan': (255, 255, 0), 'white': (255, 255, 255), 'black': (0, 0, 0),
          'gray': (125, 125, 125), 'rand': np.random.randint(0, high=256, size=(3,)).tolist(),
          'dark_gray': (50, 50, 50), 'light_gray': (220, 220, 220)}

for index, page in enumerate(pdf_data['page_list']):
    page_width = page['page_width']
    page_height = page['page_height']
    image = np.zeros((int(page_height), int(page_width), 3), dtype='uint8')
    image[:] = colors['light_gray']
    for text_item in page['text_list']:
        # bbox 출력
        cv2.rectangle(image, (int(text_item['bbox']['x1']), int(text_item['bbox']['y1'])), (int(
            text_item['bbox']['x2']), int(text_item['bbox']['y2'])), colors['red'], 1)
        # 텍스트 출력
        if text_item.get('text') != None:
            for i, line in enumerate(text_item.get('text').split('\n')): # OpenCV의 putText메소드에서 '\n'줄바꿈 처리가 잘 안돼서 수동으로 줄 단위로 잘라서 출력
                cv2.putText(image, line, (int(text_item['bbox']['x1']), int(text_item['bbox']['y1'] + 10 * (i + 1))), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.4, colors['black'], 1, cv2.LINE_AA)

    page_title = f"page {page['page_id']}"
    print(f"data/pdf_images/{filename}/page{page['page_id']}.png")
    pdf_images_path = f"data/pdf_images/{filename}"
    os.makedirs(pdf_images_path, exist_ok=True)
    # 이미지를 data/pdf_images폴더에 쓰기
    cv2.imwrite(f"{pdf_images_path}/page{page['page_id']}.png", image)
