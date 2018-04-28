# This code was adapted from sample code provided by the ETL to load images from their dataset

import bitstring
import os
from PIL import Image, ImageEnhance

t56s = '0123456789[#@:>? ABCDEFGHI&.](<  JKLMNOPQR-$*);\'|/STUVWXYZ ,%="!'
f = bitstring.ConstBitStream(filename='ETL4/ETL4C')

def read(pos=0):
    f.bytepos = pos * 2952
    r = f.readlist('2*uint:36,uint:8,pad:28,uint:8,pad:28,4*uint:6,pad:12,15*uint:36,pad:1008,bytes:21888')
    return r

total_samples = 6100
train_proportion = 0.8

training = int(total_samples * train_proportion)

if not os.path.exists('data'):
    os.makedirs('data')

if not os.path.exists('data/train'):
    os.makedirs('data/train')

if not os.path.exists('data/test'):
    os.makedirs('data/test')

for i in range(total_samples):
    r = read(i)
    path = 'data/'
    if i < training:
        path += 'train/'
    else:
        path += 'test/'

    img = Image.frombytes('F', (r[18], r[19]), r[-1], 'bit', 4)
    img = img.convert('RGB')
    img = ImageEnhance.Brightness(img)
    img = img.enhance(r[20])
    # I dump the first two characters because they aren't relevant in this dataset
    label = ''.join([t56s[c] for c in r[6:8]]).strip()

    path += label + '/'
    if not os.path.exists(path):
        os.makedirs(path)

    img.save(path + str(i) + '.jpg')