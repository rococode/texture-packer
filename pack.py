#!/usr/bin/env python3

from PIL import Image
import os
import shutil
import time
import datetime
from tqdm import tqdm

INPUT_DIR = "in"
INPUT_FILE = INPUT_DIR + os.sep + "info.txt"
SAVE_CROPS = False
CUT_DIR = "cut"
OUT_DIR = "out"
PADDING = 5

class SpriteInfo:
    def __init__(self, file_name, name, fw, fh, sx, sy, sw, sh, k):
        self.file_name = file_name
        self.name = name
        self.fw = int(fw)
        self.fh = int(fh)
        self.sx = int(sx)
        self.sy = int(sy)
        self.sw = int(sw) if int(sw) is not 0 else int(fw)
        self.sh = int(sh) if int(sh) is not 0 else int(fh)
        self.keep_shape = True if int(k) is 1 else False
        self.crop = []

def read(input_file):
    info = []
    with open(input_file, "r") as f:
        lines = f.readlines()

        for i, line in enumerate(lines):
            line = line.strip()
            if len(line) == 0 or line.find("//") == 0:
                print("skipping " + str(line))
                continue
            tmp = line.split("\t")
            data = [x for x in tmp if len(x) is not 0]
            if len(data) != 9:
                print("WARNING: FAILED TO PARSE LINE " + str(i) + ":\n\t" + str(line) + "\n\t" + str(data))
                continue
            si = SpriteInfo(data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8])
            info.append(si)
    return info

def cut(in_sprite_info, in_dir, out_dir):
    shutil.rmtree(out_dir)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    total = 0
    tq = tqdm(in_sprite_info, desc='Processed ')
    ext = ".png"
    for si in tq:
        im = Image.open(in_dir + os.sep + si.file_name + ext)
        # size of the full image
        w_pix, h_pix = im.size
        # pixels per sprite width and sprite height
        ppw, pph = w_pix / si.fw, h_pix / si.fh
        i = 0
        # max number of digits (for file name formatting)
        digits = len(str(si.sw * si.sh))
        crops = []

        # crop out each part of the sprite
        for dy in range(si.sh):
            for dx in range(si.sw):
                lx, ly = ppw * si.sx + dx * ppw, ppw * si.sy + dy * pph
                crops.append(im.crop((lx, ly, lx + ppw, ly + pph)))

        # store crops
        for crop in crops:
            si.crop.append(crop)
            if SAVE_CROPS:
                crop.save(CUT_DIR + os.sep + si.name + "_" + (("%0" + str(digits) + "d") % i) + ext)
            total += 1
            tq.set_description("Processed " + str(total) + " sprites")
            i += 1

def pack(in_sprite_info, in_dir, out_dir):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    images = [] # (image, name, w, h, x, y)
    curr_x = PADDING
    max_y = 0
    mode = None
    tq = tqdm(in_sprite_info, desc="Merging")
    for si in tq:
        if si.keep_shape:
            # write out sprite parts in the original shape but with padding
            dx = 0
            dy = 0
            total_x_size = 0
            total_y_size = 0
            max_x_size = 0
            for im in si.crop:
                mode = im.mode
                images.append((im, si, im.size[0], im.size[1], curr_x + total_x_size, PADDING + total_y_size))
                total_x_size += im.size[0] + PADDING
                max_x_size = max(max_x_size, total_x_size)
                max_y = max(max_y, total_y_size)
                dx += 1
                if dx >= si.sw:
                    dx = 0
                    total_x_size = 0
                    total_y_size += im.size[1] + PADDING
                    max_y = max(max_y, total_y_size + PADDING)
            curr_x += max_x_size
        else:
            # just put the parts of the sprite side by side
            for im in si.crop:
                mode = im.mode
                images.append((im, si, im.size[0], im.size[1], curr_x, PADDING))
                max_y = max(max_y, im.size[1] + PADDING * 2)
                curr_x += im.size[0] + PADDING
    ts = datetime.datetime.fromtimestamp(time.time()).strftime('%Y_%m_%d-%H_%M_%S')
    spritesheet = Image.new("RGBA", (curr_x, max_y), color=(178, 237, 255, 255))
    print("Creating final spritesheet with mode: {}".format(spritesheet.mode))
    for im, si, w, h, x, y in images:
        spritesheet.paste(im, (x, y, x + w, y + h))
    spritesheet.save(OUT_DIR + os.sep + "sprites_" + ts + ".png")

info = read(INPUT_FILE)
cut(info, INPUT_DIR, CUT_DIR)
pack(info, CUT_DIR, OUT_DIR)
