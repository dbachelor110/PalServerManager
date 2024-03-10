from os import makedirs
from os import path as osPath

def EXdir(file,time=1):
    """取得父層路徑的方法，輸入 time 可以向上尋找多次"""
    temp = file
    for i in range(time):
        temp = osPath.dirname(temp)
    return temp

def insureDir(path):
    """確定路徑存在，若不存在會新建路徑。"""
    if not osPath.exists(path):
        makedirs(path)

ROOTDIR = EXdir(__file__)
STATIC = osPath.join(ROOTDIR, 'static')
TEMPLATES = osPath.join(ROOTDIR, 'templates')
OUTPUT = osPath.join(ROOTDIR, 'output')
TEMP = osPath.join(OUTPUT, 'temp')
SRC = osPath.join(ROOTDIR, 'src')

insureDir(STATIC)
insureDir(TEMPLATES)
insureDir(OUTPUT)
insureDir(TEMP)
insureDir(SRC)