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
# CUT_DIR = "cut" # unused
OUT_DIR = "out"
OUT_SEPARATE_DIR = "sep"
OUT_FILE = "sprite_enum.txt"
PADDING = 5

AUTO_FILE = None
COPY_DIR = None

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
        self.final_w = 0
        self.final_h = 0

def read(input_file):
    global AUTO_FILE
    global COPY_DIR
    info = []
    with open(input_file, "r") as f:
        lines = f.readlines()

        for i, line in enumerate(lines):
            line = line.strip()
            if line.find("AUTO") == 0:
                AUTO_FILE = line[line.find(" ") + 1:]                 
                print("Found auto enum file: " + AUTO_FILE)
                continue
            if line.find("COPY") == 0:
                COPY_DIR = line[line.find(" ") + 1:]                 
                print("Found copy dir: " + COPY_DIR)
                continue
            if len(line) == 0 or line.find("//") == 0:
                # print("skipping " + str(line))
                continue
            tmp = line.split("\t")
            data = [x for x in tmp if len(x) is not 0]
            if len(data) != 9:
                print("WARNING: FAILED TO PARSE LINE " + str(i) + ":\n\t" + str(line) + "\n\t" + str(data))
                continue
            si = SpriteInfo(data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8])
            info.append(si)
    return info

def cut(in_sprite_info, in_dir):
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

def separate(in_sprite_info, out_dir):
    global COPY_DIR
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    tq = tqdm(in_sprite_info, desc="Separating")
    for si in tq:
        images = []
        curr_x = 0
        curr_y = 0
        dx = 0
        max_y = 0
        max_x = 0
        padded_y = False
        for im in si.crop:
            if not padded_y:
                curr_y += PADDING
                padded_y = True
            curr_x += PADDING
            images.append((curr_x, curr_y, im))
            curr_x += im.size[0] + PADDING
            max_x = max(max_y, curr_x)
            max_y = max(max_y, im.size[1])
            dx += 1
            if dx >= si.sw:
                dx = 0
                curr_x = 0
                curr_y += max_y + PADDING
                padded_y = False

        # sprite = Image.new("RGBA", (max_x, curr_y), color=(178, 237, 255, 255))
        sprite = Image.new("RGBA", (max_x, curr_y), color=(178, 237, 255, 0))
        for cx, cy, im in images:
            sprite.paste(im, (cx, cy, cx + im.size[0], cy + im.size[1]))
        sprite.save(out_dir + os.sep + si.name + ".png")
        sprite.save(COPY_DIR + os.sep + si.name + ".png")
        si.final_w = sprite.size[0]
        si.final_h = sprite.size[1]


def pack(in_sprite_info, in_dir, out_dir):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    if not os.path.exists(out_sep):
        os.makedirs(out_sep)
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

def enum(in_sprite_info, out_enum):
    global AUTO_FILE
    lines = []
    for si in in_sprite_info:
        s = '    ' + si.name.upper()
        s += '('
        s += ', '.join([str(x) for x in ['"' + si.name + '.png"', si.final_w, si.final_h, si.sw, si.sh, PADDING]])
        s += '),\n'
        lines.append(s)
    with open(out_enum, "w") as out:
        out.writelines(lines)
        print("Write to {}".format(out.name))
    if AUTO_FILE is not None:
        with open(AUTO_FILE, "r") as enum:
            auto_lines = enum.readlines()
            final_lines = []
            auto = False
            for line in auto_lines:
                if line.find("// START AUTO") > -1:
                    auto = True
                    final_lines.append(line)
                    final_lines.append('\n')
                    for l in lines:
                        final_lines.append(l)
                    final_lines.append('\n')
                elif line.find("// END AUTO") > -1:
                    final_lines.append(line)
                    auto = False
                elif auto:
                    continue
                else:
                    final_lines.append(line)
        # print(final_lines)
        with open(AUTO_FILE, "w") as enum:
            enum.writelines(final_lines)


info = read(INPUT_FILE)
cut(info, INPUT_DIR)
separate(info, OUT_SEPARATE_DIR)
# pack(info, CUT_DIR, OUT_SEPARATE_DIR)
enum(info, OUT_FILE)
