
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


#################################
#   BYTE ARRAY ENCODED INTO PNG
#
#   [ 58 54 4f 46 49 4e 46 4f ] [ DATA_SIZE ] [ ....... DATA ....... ] [ PADDING ]
#    8 bytes                     4 bytes        DATA_SIZE bytes          various   
#
#################################
# TODO : Replace the magick number by a checksum on the data

#!/usr/bin/python3

import os
import argparse
import math
import hashlib
import random
from PIL import Image

BYTES_PER_PIXEL = 4 #RGBA
HASH_LEN = 64
SIZE_LEN = 4


def xoring( data, key ):
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


hasher = hashlib.sha512()

# PARSING COMMAND LINE ARGUMENTS
parser = argparse.ArgumentParser(description="This script converts any file into a PNG image.")
parser.add_argument("file", help="file to convert")
parser.add_argument("output", help="output filename")
# TODO : Real optional arg without parameter!
parser.add_argument("-x","--extract", action='store_true', help="extract file from png", required=False)
args = parser.parse_args()

# SANITY
if not os.path.exists( args.file ):
    print("File " +  args.file + " does not exist!")
    exit(-1)

# ENCODING
if not args.extract:
    # PROCESSING
    # Reading file     
    size_data = os.path.getsize( args.file )
    with open(args.file, 'rb') as file_in:
        data = bytearray( size_data.to_bytes(SIZE_LEN,byteorder='little') + bytearray( file_in.read() ) )
    # checksum  
    hasher.update( data )
    hash = hasher.digest()
    # Padding the data
    random.seed(os.urandom(4))
    dim_img = math.ceil( math.sqrt( len(data) / BYTES_PER_PIXEL ) )
    for i in range(dim_img*dim_img*BYTES_PER_PIXEL - len(data) ):
        data.append( random.getrandbits(8) )
    # XORing with hash
    data = bytearray(hash) + xoring( data, hash )
    # Interpreting as a raw image and saving
    size_img = ( dim_img, dim_img )
    img = Image.frombytes('RGBA', size_img, bytes(data) )
    # TODO : Test if output folder exists
    img.save(args.output)

# EXTRACTING
else:
    raw = Image.open(args.file).tobytes()
    hash = raw[:HASH_LEN]
    # xoring
    raw = xoring( bytearray(raw[HASH_LEN:]), hash )
    # reading data size
    begin_data = SIZE_LEN
    size_data = int.from_bytes( raw[:SIZE_LEN ], byteorder='little' )
    end_data = begin_data + size_data
    if end_data > len(raw):
        print("This is not a PNGized image!")
        exit(-1)
    # checking hash
    hasher.update( raw[:end_data] )
    if hash != hasher.digest():
        print("This is not a PNGized image!")
        exit(-1)
    with open(args.output,"wb") as file_out:
        file_out.write( raw[begin_data:end_data] )
        
        
        

