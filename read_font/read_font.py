#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Needs freetype-py>=1.0

# For more info see:
# http://dbader.org/blog/monochrome-font-rendering-with-freetype-and-python

# The MIT License (MIT)
#
# Copyright (c) 2013 Daniel Bader (http://dbader.org)
# Copyright (c) 2016 Bogdan Marinescu (http://bogdanm.me) - read_font.py
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import freetype
import sys
import json
import argparse
import os
import operator

class Bitmap(object):
    """
    A 2D bitmap image represented as a list of byte values. Each byte indicates the state
    of a single pixel in the bitmap. A value of 0 indicates that the pixel is `off`
    and any other value indicates that it is `on`.
    """
    def __init__(self, width, height, pixels):
        self.width = width
        self.height = height
        self.pixels = pixels

    def __repr__(self):
        """Return a string representation of the bitmap's pixels."""
        rows = ''
        fmt = "%%0%dd " % len(str(self.height))
        for y in range(self.height):
            rows += fmt % y
            for x in range(self.width):
                rows += '*' if self.pixels[y * self.width + x] else '.'
            rows += '\n'
        return rows

class Glyph(object):
    def __init__(self, pixels, width, height, top, char):
        self.bitmap = Bitmap(width, height, pixels)
        self.char = char

        # The glyph bitmap's top-side bearing, i.e. the vertical distance from the
        # baseline to the bitmap's top-most scanline.
        self.top = top

    @property
    def width(self):
        return self.bitmap.width

    @property
    def height(self):
        return self.bitmap.height

    @staticmethod
    def from_glyphslot(slot, char):
        """Construct and return a Glyph object from a FreeType GlyphSlot."""
        pixels = Glyph.unpack_mono_bitmap(slot.bitmap)
        width, height = slot.bitmap.width, slot.bitmap.rows
        top = slot.bitmap_top

        return Glyph(pixels, width, height, top, char)

    @staticmethod
    def unpack_mono_bitmap(bitmap):
        """
        Unpack a freetype FT_LOAD_TARGET_MONO glyph bitmap into a bytearray where each
        pixel is represented by a single byte.
        """
        # Allocate a bytearray of sufficient size to hold the glyph bitmap.
        data = bytearray(bitmap.rows * bitmap.width)

        # Iterate over every byte in the glyph bitmap. Note that we're not
        # iterating over every pixel in the resulting unpacked bitmap --
        # we're iterating over the packed bytes in the input bitmap.
        for y in range(bitmap.rows):
            for byte_index in range(bitmap.pitch):

                # Read the byte that contains the packed pixel data.
                byte_value = bitmap.buffer[y * bitmap.pitch + byte_index]

                # We've processed this many bits (=pixels) so far. This determines
                # where we'll read the next batch of pixels from.
                num_bits_done = byte_index * 8

                # Pre-compute where to write the pixels that we're going
                # to unpack from the current byte in the glyph bitmap.
                rowstart = y * bitmap.width + byte_index * 8

                # Iterate over every bit (=pixel) that's still a part of the
                # output bitmap. Sometimes we're only unpacking a fraction of a byte
                # because glyphs may not always fit on a byte boundary. So we make sure
                # to stop if we unpack past the current row of pixels.
                for bit_index in range(min(8, bitmap.width - num_bits_done)):

                    # Unpack the next pixel from the current glyph byte.
                    bit = byte_value & (1 << (7 - bit_index))

                    # Write the pixel to the output bytearray. We ensure that `off`
                    # pixels have a value of 0 and `on` pixels have a value of 1.
                    data[rowstart + bit_index] = 1 if bit else 0

        return data


class Font(object):
    def __init__(self, filename, size):
        self.face = freetype.Face(filename)
        self.face.set_pixel_sizes(0, size)

    def glyph_for_character(self, char):
        # Let FreeType load the glyph for the given character and tell it to render
        # a monochromatic bitmap representation.
        self.face.load_char(char, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_MONO)
        return Glyph.from_glyphslot(self.face.glyph, char)

    def render_character(self, char):
        glyph = self.glyph_for_character(char)
        return glyph

def main():
    parser = argparse.ArgumentParser(description="Reads a font, outputs char data in JSON format")
    parser.add_argument("-f", dest="font", required="True", help="Font file")
    parser.add_argument("-s", dest="size", type=int, required="True", help="Font size")
    parser.add_argument("-o", dest="output", help="Output JSON file")
    parser.add_argument("-v", dest="verbose", action="store_true", help="Verbose operation")
    parser.add_argument("-r", dest="range", help="Range of char to decode (low,high)")
    parser.add_argument("-c", dest="chars", action="append", help="Chars to decode as a string")
    parser.add_argument("--display-chars", dest="display_chars", action="store_true", help="Display chars on screen (implies verbose)")
    args = parser.parse_args()

    # Try to figure out the default directory for fonts
    default_font_dir = None
    if sys.platform.startswith("win"):
        windir = os.getenv("SystemRoot", None) or os.getenv("windir", None)
        if windir:
            default_font_dir = os.path.join(windir, "fonts")
            if not os.path.isdir(default_font_dir):
                default_font_dir = None

    # Validate arguments
    fontfile = args.font
    if not os.path.isfile(fontfile):
        # Try to reopen with the default base directory
        fontfile2 = os.path.join(default_font_dir or '', fontfile)
        if not os.path.isfile(fontfile2):
            sys.stderr.write("Unable to find '%s'" % fontfile)
            sys.exit(1)
        else:
            print "Using font '%s'" % fontfile2
            fontfile = fontfile2

    if (args.range is not None and args.chars is not None) or (args.range is None and args.chars is None):
        sys.stderr.write("You must specify exactly one of '-c' or '-r'.\n")
        sys.exit(1)
    clist = []
    if args.range is not None:
        d = args.range.split(",")
        if len(d) != 2:
            sys.stderr.write("Invalid range '%s' for '-r', must be 'low,high'.\n" % args.range)
            sys.exit(1)
        try:
            low, high = int(d[0]), int(d[1])
        except:
            sys.stderr.write("Invalid range '%s' for '-r', must be 'low,high'.\n" % args.range)
            sys.exit(1)
        if low > high:
            low, high = high, low
        if low < 0 or high < 0 or low > 255 or high > 255:
            sys.stderr.write("Invalid range '%s' for '-r', must be between 0 and 255.\n" % args.range)
            sys.exit(1)
        clist = range(low, high + 1)
    if args.chars is not None:
        clist = sorted([ord(c) for c in set(reduce(operator.add, args.chars))])

    fnt = Font(fontfile, args.size)

    # Get the representations of the specified chars
    fdata, chars = [], []
    for ccode in clist:
        c = chr(ccode)
        ch = fnt.render_character(c)
        chars.append(ch)
        # Get the representation of the given char as an array of 'height' strings of 'width' size each
        # (this makes it easy to visualize the strings)
        t, a = '', []
        for e in ch.bitmap.pixels:
            t = t + ("." if e == 0 else "*")
            if len(t) == ch.bitmap.width:
                a.append(t)
                t = ''
        fdata.append({"char": c, "width": ch.bitmap.width, "height": ch.bitmap.height, "top": ch.top, "data": a})

    # Display char data if requested
    for ch in chars:
        c = ch.char
        if args.display_chars or args.verbose:
            print "Char: '%s' Code: %d Width: %d Height: %d Top: %d" % (c, ord(c), ch.bitmap.width, ch.bitmap.height, ch.top)
        if args.display_chars:
            print(repr(ch.bitmap))

    # Print statistics in verbose mode
    if args.display_chars or args.verbose:
        heights, widths = [e.bitmap.height for e in chars], [e.bitmap.width for e in chars]
        print "Min height:%-3d Max height: %-3d" % (min(heights), max(heights))
        print "Min width: %-3d Max width:  %-3d" % (min(widths), max(widths))

    # Write char data if needed
    if args.output is not None:
        with open(args.output, "wt") as f:
            json.dump(fdata, f, ensure_ascii=True, indent=4)
        print "Wrote char data to '%s'" % args.output

if __name__ == "__main__":
    main()
