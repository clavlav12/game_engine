import pyperclip
from glob import glob
from tkinter import filedialog
from tkinter import *
from os.path import basename
root = Tk()
root.withdraw()
folder_selected = filedialog.askdirectory()
lst = glob(folder_selected+'/*.mp3')
lst = '\n'.join([basename(file) for file in lst])
pyperclip.copy(lst[:int(len(lst)/2)])
input()
pyperclip.copy(lst[int(len(lst)/2):])

