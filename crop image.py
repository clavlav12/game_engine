from PIL import Image
from glob import glob as files_in_dir
import os

for file in files_in_dir(r'animation/fighter/PNG/PNG Sequences/Dying' + '\\*'):
    im = Image.open(file)
    im.getbbox()  # (64, 89, 278, 267)
    im2 = im.crop(im.getbbox())
    im2.save(file)
