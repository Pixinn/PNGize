#!/usr/bin/env python3
#
# pyConvert.py
# Copyright (C) 2016 Christophe Meneboeuf <christophe@xtof.info>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


import argparse
import hashlib
import io
import math
import os
import random

from PIL import Image


BYTES_PER_PIXEL = 4  # RGBA.
SIZE_LEN = 4         # Space in bytes used to encode sizes.
CHUNK_LEN = 2 ** 21  # Size of chunke used to compute the file hash.
DIM_PNG_MIN = 16     # The resulting PNG will be at least 16x16.


def Error(msg, err_code):
  '''Report an error then exit.'''
  print(msg)
  exit(err_code)


def Xoring(data, key):
  '''Xor the <data> bytearray with the <key> bytearray.

  If <key> is smaller than <data>, <key> is repeated enough times to match
  <data>'s size.
  '''
  xored = 0
  idx_key = 0
  len_data = len(data)
  len_key = len(key)
  while xored < len_data:
    data[ xored ] ^= key[ idx_key ]
    xored += 1
    idx_key += 1
    if idx_key == len_key:
      idx_key = 0
  return data


def ExtractPNGFile(src_path, dst_path, hash_method):
  '''Extract the file encoded as PNG.

  Arguments are
   * src_path:    the PNG file to extract.
   * dst_path:    the output filename, if None then the filename encoded in the
                  PNG file is used.
   * hash_method: explicit.
  '''
  raw = bytearray(Image.open(src_path).tobytes())
  hash_len = hash_method.digest_size
  checksum = raw[:hash_len]

  # Xoring
  raw = Xoring(raw[hash_len:], checksum)

  # Reading header
  filename_size = int.from_bytes(raw[:SIZE_LEN], byteorder = 'little')
  cursor = SIZE_LEN
  if not dst_path:
    dst_path = raw[cursor:cursor + filename_size].decode(encoding = 'UTF-8')
  cursor += filename_size
  data_size = int.from_bytes(raw[cursor:cursor + SIZE_LEN],
                             byteorder = 'little')
  cursor += SIZE_LEN
  data_end = cursor + data_size
  if data_end > len(raw):
    Error("This is not a PNGized image! wrong size", -2)

  # Checking hash
  hash_method.update(raw[:data_end] )
  if checksum != hash_method.digest():
    Error("This is not a PNGized image! wrong checksum", -3)

  with io.BufferedWriter(open(dst_path, 'wb')) as dst:
    dst.write(raw[cursor:data_end])


def EncodeAsPNG(src_path, dst_path, hash_method):
  '''Encode the given file as a PNG.

  Arguments are
   * src_path:    the file to encode.
   * dst_path:    the output filename, if None then '.png' is appended to the
                  input filename.
   * hash_method: explicit.
  '''
  # [ header ] : [ filename size ] [ filename utf8 ] [ file size ]
  filename = bytes(os.path.basename(src_path), encoding = 'utf-8')
  filename_size = len(filename).to_bytes(SIZE_LEN, byteorder = 'little')
  filesize = os.path.getsize(src_path).to_bytes(SIZE_LEN, byteorder = 'little')

  data = bytearray()
  data.extend(filename_size)
  data.extend(filename)
  data.extend(filesize)
  hash_method.update(data)

  with io.BufferedReader(open(src_path, 'rb')) as src:
    chunk = src.read(CHUNK_LEN)
    while chunk:
      data.extend(chunk)
      hash_method.update(chunk)
      chunk = src.read(CHUNK_LEN)

  # Padding
  random.seed(os.urandom(4))
  dim_img = math.ceil(math.sqrt(len(data) / BYTES_PER_PIXEL))
  dim_img = max(dim_img, DIM_PNG_MIN)
  to_pad = (dim_img * dim_img * BYTES_PER_PIXEL) - len(data)
  for i in range(to_pad):
    data.append(random.getrandbits(8))

  raw = bytearray(hash_method.digest())
  data = Xoring(data, raw)
  raw.extend(data)

  # Interpreting as a raw image
  size_img = dim_img, dim_img
  img = Image.frombytes('RGBA', size_img, bytes(raw))
  if not dst_path: dst_path = src_path + '.png'
  img.save(dst_path)


'''Converts any file to PNG and back.

The format of the data encoded in the PNG is:

  [ hash ] [ header ] [ file content ] [ padding ]
           |---------- XORed with hash ----------|

where

  [ hash ] is the sha512 of [ header ] [ file content ]
  [ header ] is made of [ filename size ] [ filename utf8 ] [ content size ]
  [ padding ] is random data added to make the resulting PNG image square

Sizes are encoded using SIZE_LEN bytes.
'''
if __name__ == '__main__':
  parser = argparse.ArgumentParser(
      description = 'Converts any file into a PNG image and back.')
  parser.add_argument('file', help = 'file to manipulate')
  parser.add_argument('-o','--output', help = 'output filename')
  parser.add_argument('-x','--extract', action = 'store_true',
                      help = "extract file from png", default = False)

  args = parser.parse_args()
  if not os.path.exists(args.file):
    Error('File {} does not exist!'.format(args.file), -1)

  if args.extract:
    ExtractPNGFile(args.file, args.output, hashlib.sha512())
  else:
    EncodeAsPNG(args.file, args.output, hashlib.sha512())
