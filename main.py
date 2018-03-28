import os
import sys
import re
import time
import importlib
importlib.reload(sys)

from pdfminer.pdfparser import PDFParser,PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LTTextBoxHorizontal,LAParams,LTChar,LTAnon,LTTextBox
from pdfminer.pdfinterp import PDFTextExtractionNotAllowed


sentence = []
sentenceList = []
information = []

reword = open("reserved_word.txt", 'r', encoding='utf-8').read().split('\n')
pointless = open("pointless_line.txt", 'r', encoding='utf-8').read().split('\n')

def _dictionary_():
    global sentence
    global sentenceList

    ltext = {}

    for page in sentence:
        pindex = sentence.index(page)
        ltext.update({pindex:{}})
        for y in page:
            lindex = page.index(y)
            ltext[pindex].update({round(y,2):sentenceList[pindex][lindex]})
        sorted(ltext[pindex])
    sentecne = []
    sentenceList = []
    return ltext


def parse(pdf_path, object_path):
    start = time.time()
    
    global sentence
    global sentenceList
    
    fp = open(pdf_path, 'rb')
    pr = PDFParser(fp)
    doc = PDFDocument()

    pr.set_document(doc)
    doc.set_parser(pr)

    doc.initialize()
    if not doc.is_extractable:
        raise PDFTextExtractionNotAllowed
    else:
        rsmanager = PDFResourceManager()
        laparams = LAParams(line_overlap=0.05)
        device = PDFPageAggregator(rsmanager, laparams=laparams)
        interpreter = PDFPageInterpreter(rsmanager, device)
        charlist = []
        i = 0
        for page in doc.get_pages():    
            interpreter.process_page(page)
            layout = device.get_result()         

            if not i in sentence:
                sentence.append([])
                sentenceList.append([])

            for x in list(layout):
                if isinstance(x, LTTextBoxHorizontal):
                    for line in x:
                        for char in line:
                            if isinstance(char, LTChar) :
                                _sentence_(char_matrix=char.matrix, char_text=char.get_text(), page=i)
            
            _merge_horizontal_(i)
            i += 1
        
        
        ltext = _dictionary_()
        get_information(ltext)

        end = time.time()
        process_time = end - start
        print('time:'+ str(process_time)+'\n')


def _sentence_(char_matrix, char_text, page=0):
    # sscx = sentence start coordinate x
    # secx = sentence end coordinate x
    # scy = sentence l coordinate y
    # ccx = char coordinate x
    scy = char_matrix[5]
    ccx = round(char_matrix[4],2)

    global sentence
    global sentenceList
    
    is_horizontal = False

    # Is there this line
    # 1.1 is otolerance scope
    for sn in sentence[page]:
        if abs(sn-scy) < 1.1 :
            sentenceIndex = sentence[page].index(sn)
            sentence[page][sentenceIndex] = min(scy, sn)
            is_horizontal = True
            break

    if not is_horizontal :
        sentence[page].append(scy)
        sentenceIndex = sentence[page].index(scy)
        sentenceList[page].append([])
        # record the start and end of the sentence, and the context
        # [ccx, ccx, char_text]
        #   |    |       |
        # start  end    text
        sentenceList[page][sentenceIndex].append([ccx, ccx, char_text])
    else:
        i = 0
        mdj = False

        #is_one_sentence()
        ise = lambda x, y, z: x - y < z and x - y > 0
        
        for s in sentenceList[page][sentenceIndex]:
            sscx = s[0]
            secx = s[1]
            mdj = True

            if ccx >= sscx and ccx <= secx:
                break
            elif ise(ccx, secx, 8): 
                sentenceList[page][sentenceIndex][i][1] = ccx
                sentenceList[page][sentenceIndex][i][2] = s[2] + char_text
                break  
            elif ise(sscx, ccx, 8):
                sentenceList[page][sentenceIndex][i][0] = ccx
                sentenceList[page][sentenceIndex][i][2] = char_text + s[2]
                break
            else:
                mdj = False
        
            i += 1

        if not mdj:
            sentenceList[page][sentenceIndex].append([ccx, ccx, char_text])

    return


def _merge_horizontal_(page=0):
    global sentence
    global sentenceList

    for y in sentence[page]:
        s_index = sentence[page].index(y)

        merge = False
        newList = []
        delList = []
        saveList = []
        sentenceList[page][s_index].sort()
        tmp = sentenceList[page][s_index]
        
        for l in sentenceList[page][s_index]:
            if l in delList:
                continue

            tmp =  [i for i in tmp if i not in saveList and i not in delList]

            tmp += newList
            tmp.sort()
            for l2 in tmp:
                if l == l2:
                    continue
                else:
                    # 0: start coordinate
                    # 1: end coordinate
                    # 2: text
                    if l2[0]-l[1] > 0 and l2[0]-l[1] < 80:
                        new = [l[0], l2[1], l[2]+l2[2]]
                        merge = True
                        delList.append(l)
                        delList.append(l2)
                        if l2 in newList:
                            newList.remove(l2) 
                        newList.append(new)
                        break
                    elif l[0]-l2[1] > 0 and l[0]-l2[1] < 80:
                        new = [l2[0], l[1], l2[2]+l[2]]
                        merge = True
                        delList.append(l)
                        delList.append(l2)
                        if l2 in newList:
                            newList.remove(l2)
                        newList.append(new)
                        break
            if not merge:
                saveList.append(l)

        sentenceList[page][s_index] = saveList + newList
        

def get_information(ltext={}):
    if not ltext:
        print('There are no information, Text is NULL!')
        return False
    else:
        ltext = _merge_vertical_(ltext)


def _merge_vertical_(ltext):
    
    def tlist(text):
        global reword

        re_line_1 = re.compile(r"\s*[^\s]+\s*:\s*[^\s]*")

        if re_line_1.search(text.strip()) != None :
            reserve = False
            for reserved in reword:
                if reserved in text:
                    reserve = True
                    break
            if reserve:
                return text
            else:
                return ""
        else:
            return text

    def easyclear(text):

        global information

        deleted = False

        re_contract = re.compile(r"N°\s*(de\s)?(contrat|police|police/ordre|ordre)\s*:\s*\w*", re.I)
        re_sinistre = re.compile(r"N°\s*(de\s)?sinistre\s*:\s*\w*", re.I)
        re_date = re.compile(r"date\s*(de\s)?(sinistre|événement)\s*:\s*\d{2}/\d{2}/\d{2,4}", re.I)
        re_specialsymbols =re.compile(r"\s*(\-|\_){5,}\s*", re.I)
        

        if len(text.strip())<2:
            deleted = True
        elif re_contract.search(text) != None:
            information.append(re_contract.search(text).group(0))
            deleted = True
        elif re_sinistre.search(text) != None:
            information.append(re_sinistre.search(text).group(0))
            deleted = True
        elif re_date.search(text) != None:
            information.append(re_date.search(text).group(0))
            deleted = True
        else:
            text = re_specialsymbols.sub(" ", text)

            if "!" in text:
                tmpList = text.strip().split('!')
                text = ""
                for t in tmpList:
                    text += ' '+tlist(t)
            else:
                text = tlist(text)

            return text
        return deleted

    ltext = vertical_align(ltext)
    for page in ltext:
        y = sorted(ltext[page], reverse=True)
        i = 0
        iy = []
        while i < len(y):
            for text in ltext[page][y[i]]:
                clearReturn = easyclear(text[2])
                if type(clearReturn) == str:
                    index = ltext[page][y[i]].index(text)
                    newtext = clearReturn.strip()
                    if newtext == '':
                        ltext[page][y[i]].remove(text)
                    else:
                        ltext[page][y[i]][index][2] = newtext
                elif clearReturn:
                    ltext[page][y[i]].remove(text)
                if len(ltext[page][y[i]]) == 0:
                    del ltext[page][y[i]]
            i += 1
    for g in ltext[0]:
        print(ltext[0][g])
    return ltext


def vertical_align(ltext):
    for page in ltext:
        y = sorted(ltext[page], reverse=True)
        i = 0
        iy = [] #index y ---> i
        while i < len(y)-1:
            if y[i] not in iy:
                if y[i] - y[i+1] < 1.5:
                    ltext[page][y[i]] = ltext[page][y[i]]+ltext[page][y[i+1]]
                    ltext[page][y[i]].sort()
                    iy.append(y[i+1])
            i += 1
        
        for indx in iy:
            del ltext[page][indx]
  
    return ltext

if __name__ == '__main__':
    object_path='test.txt'
    pdf_path='PDF\\RAPPORT_3156791_130763.pdf'
    parse(object_path=object_path, pdf_path=pdf_path)
