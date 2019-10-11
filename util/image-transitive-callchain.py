#!/usr/bin/env python

import sys
import json
import array
import zlib
import struct

class PNGData(object):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.scanlineWidth = (((width + 7) >> 3) + 1)

        # raw_data: each scanline must start with byte 0
        scanline = array.array('B', b'\x00' * self.scanlineWidth)

        data = array.array('B')
        for i in range(0, height):
            data.extend(scanline)

        self.data = data


    def set_bit(self, x, y):
        idx = y * self.scanlineWidth + (x >> 3) + 1
        self.data[idx] |= (0x80 >> (x & 0x7))


    @staticmethod
    def png_pack(png_file, png_tag, data):
        crc = zlib.crc32(data, zlib.crc32(png_tag)) & 0xFFFFFFFF

        png_file.write(struct.pack("!I", len(data)))
        png_file.write(png_tag)
        png_file.write(data)
        png_file.write(struct.pack("!I", crc))


    def write_png(self, file_name):
        with open(file_name, "w") as png_file:
            # 8 byte PNG header
            png_file.write(b'\x89PNG\r\n\x1a\n')

            # Grayscale image, 1 bit / pixel, inflate compression, basic filter, no interlace
            PNGData.png_pack(png_file, b'IHDR', struct.pack("!2I5B", self.width, self.height, 1, 0, 0, 0, 0))
            PNGData.png_pack(png_file, b'IDAT', zlib.compress(self.data, 9))
            PNGData.png_pack(png_file, b'IEND', b'')


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("Usage: image-transitive-cg.py nodes_filename callchain_filename")

    with open(sys.argv[1]) as nodes_fp:
        nodes_data = json.load(nodes_fp)

    with open(sys.argv[2]) as json_fp:
        json_data = json.load(json_fp)

    size = len(nodes_data)

    nodes_map = {}
    for node in nodes_data:
        nodes_map[node["pos"]] = node["id"]

    id_map = {}
    for node in json_data["nodes"]:
        other_id = nodes_map.get(node["pos"], None)
        if other_id != None:
            id_map[node["id"]] = other_id

    # Free memory
    nodes_map = None
    nodes_data = None

    data = PNGData(size, size)

    for call_chain in json_data["call_chains"]:
        new_call_chain = tuple(id_map[idx] for idx in call_chain if idx in id_map)
        # print("%s -> %s" % (call_chain, new_call_chain))
        length = len(new_call_chain)

        for i in range(0, length):
            for j in range(i + 1, length):
                data.set_bit(new_call_chain[j], new_call_chain[i])

    data.write_png('result.png')
