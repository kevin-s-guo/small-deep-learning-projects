# Code also adapted from ETLCD sample code for loading data

import struct
import os
from PIL import Image, ImageEnhance

sz_record = 8199

def read_record_ETL8G(f):
    s = f.read(sz_record)
    r = struct.unpack('>2H8sI4B4H2B30x8128s11x', s)
    iF = Image.frombytes('F', (128, 127), r[14], 'bit', 4)
    iL = iF.convert('L')
    return r + (iL,)

def read_hiragana():
    hiragana = []
    num = 0

    for j in range(1, 33):
        filename = 'ETL8G/ETL8G_{:02d}'.format(j)
        with open(filename, 'rb') as f:
            for id_dataset in range(5):
                for i in range(956):
                    r = read_record_ETL8G(f)
                    if b'.HIRA' in r[2]:
                        img = r[-1].convert('RGB')
                        enhancer = ImageEnhance.Brightness(img)
                        img = enhancer.enhance(35)
                        label = str(r[2]).split("'")[1]
                        label = label.split('.')[0]
                        num += 1
                        if label != 'KAI' and label != 'HEI' and label != 'JI' and label != 'ZU':
                            hiragana.append((label, img))
    return hiragana


hiragana = read_hiragana()

train_proportion = 0.8

training = int(len(hiragana) * train_proportion)

if not os.path.exists('data2'):
    os.makedirs('data2')

if not os.path.exists('data2/train'):
    os.makedirs('data2/train')

if not os.path.exists('data2/test'):
    os.makedirs('data2/test')

for i in range(len(hiragana)):
    path = 'data2/'

    if i < training:
        path += 'train/'
    else:
        path += 'test/'

    path += hiragana[i][0] + '/'
    if not os.path.exists(path):
        os.makedirs(path)

    hiragana[i][1].save(path + str(i) + '.jpg')