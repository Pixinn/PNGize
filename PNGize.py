
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
#   [ SHA512(DATA_SIZE & DATA) ] [ FILENAME_SIZE ] [  FILENAME  ] [ DATA_SIZE ] [ ....... DATA ....... ] [ PADDING ]
#    >          8 bytes       <   >    4 bytes  <  >  F_Z bytes < > 4 bytes   < > DATA_SIZE bytes      < > various <   
#                                 | ............................. XORed by SHAS512 ................................| 
#
#################################

#!/usr/bin/env python3

import os
import argparse
import math
import hashlib
import random
from PIL import Image

BYTES_PER_PIXEL = 4 #RGBA
HASH_LEN = 64
SIZE_LEN = 4
DIM_PNG_MIN = 16

def Error( msg, err_code ):
    print( msg )
    exit(err_code)

def Xoring( data, key ):
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


Hasher = hashlib.sha512()

# PARSING COMMAND LINE ARGUMENTS
parser = argparse.ArgumentParser(description="This script converts any file into a PNG image.")
parser.add_argument("file", help="file to convert")
parser.add_argument("-o","--output", help="output filename", required=False)
parser.add_argument("-x","--extract", action='store_true', help="extract file from png", required=False)
args = parser.parse_args()

# SANITY
if not os.path.exists( args.file ):
    Error("File " +  args.file + " does not exist!", -1 )

# ENCODING
if not args.extract:
    # PROCESSING
    # Reading file     
    size_data = os.path.getsize( args.file )
    with open(args.file, 'rb') as file_in:
        data = bytearray( size_data.to_bytes(SIZE_LEN,byteorder='little') + bytearray( file_in.read() ) )
    # checksum  
    Hasher.update( data )
    hash = Hasher.digest()
    # Padding the data
    random.seed(os.urandom(4))
    dim_img = math.ceil( math.sqrt( len(data) / BYTES_PER_PIXEL ) )
    to_pad = dim_img*dim_img*BYTES_PER_PIXEL - len(data)
    for i in range( to_pad ):
        data.append( random.getrandbits(8) )
    if len( data ) < (DIM_PNG_MIN*DIM_PNG_MIN*BYTES_PER_PIXEL):    
        to_pad = DIM_PNG_MIN*DIM_PNG_MIN*BYTES_PER_PIXEL - len( data )
        dim_img = DIM_PNG_MIN
        for i in range( to_pad ):
            data.append( random.getrandbits(8) )
    # XORing with hash
    data = bytearray(hash) + Xoring( data, hash )
    # Interpreting as a raw image and saving
    size_img = ( dim_img, dim_img )
    img = Image.frombytes('RGBA', size_img, bytes(data) )
    # TODO : Test if output folder exists
    img.save(args.output)

# EXTRACTING
else:
    raw = Image.open(args.file).tobytes()
    hash = raw[:HASH_LEN]
    # Xoring
    raw = Xoring( bytearray(raw[HASH_LEN:]), hash )
    # reading data size
    begin_data = SIZE_LEN
    size_data = int.from_bytes( raw[:SIZE_LEN ], byteorder='little' )
    end_data = begin_data + size_data
    if end_data > len(raw):
        Error("This is not a PNGized image!", -2 )

    # checking hash
    Hasher.update( raw[:end_data] )
    if hash != Hasher.digest():
        Error("This is not a PNGized image!", -3 )
    with open(args.output,"wb") as file_out:
        file_out.write( raw[begin_data:end_data] )
        
        
        

