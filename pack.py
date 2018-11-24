#!/usr/bin/env python3

from PIL import Image
import os
import shutil
import time
import datetime
from tqdm import tqdm

INPUT_DIR = "in"
CUT_DIR = "cut"
OUT_DIR = "out"
PADDING = 2

def cut(in_dir, out_dir):
    shutil.rmtree(out_dir)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    total = 0
    tq = tqdm(os.listdir(in_dir), desc='Processed ')
    for f in tq:
        dim = f[f.rfind("_") + 1:]
        dim = dim[:dim.find(".")]
        file_name = f[:f.rfind(".")]
        ext = f[f.rfind("."):]
        x = int(dim[0:dim.find("x")]) # size in sprites width
        y = int(dim[dim.find("x") + 1:]) # size in sprites height
        im = Image.open(in_dir + os.sep + f)
        w, h = im.size
        # print("size", w, h, x, y)
        sprite_w = int(w / x)
        sprite_h = int(h / y)
        i = 0
        num = int(w * h / (sprite_w * sprite_h))
        # print("num", num)
        digits = max(2, len(str(num)))
        for dx in range(0, w, sprite_w):
            for dy in range(0, h, sprite_h):
                crop = im.crop((dx, dy, dx + sprite_w, dy + sprite_h))
                crop.save(CUT_DIR + os.sep + file_name + "_" + (("%0" + str(digits) + "d") % i) + ext)
                i += 1
                total += 1
                tq.set_description("Processed " + str(total) + " sprites")


def pack(in_dir, out_dir):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    images = [] # (image, name, w, h, x, y)
    curr_x = 0
    max_y = 0
    mode = None
    for f in os.listdir(in_dir):
        im = Image.open(in_dir + os.sep + f)
        mode = im.mode
        images.append((im, f, im.size[0], im.size[1], curr_x, 0))
        max_y = max(max_y, im.size[1])
        curr_x += im.size[0]
    ts = datetime.datetime.fromtimestamp(time.time()).strftime('%Y_%m_%d-%H_%M_%S')
    print("Creating final spritesheet with mode: {}".format(mode))
    spritesheet = Image.new(mode, (curr_x, max_y))
    for im, name, w, h, x, y in images:
        spritesheet.paste(im, (x, y, x + w, y + h))
    spritesheet.save(OUT_DIR + os.sep + "sprites_" + ts + ".png")

cut(INPUT_DIR, CUT_DIR)
pack(CUT_DIR, OUT_DIR)
