
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
from PIL import Image

MAGICK_NUMBER = bytes([0x58, 0x54, 0x4f, 0x46, 0x49, 0x4e, 0x46, 0x4f])

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
if args.extract == None:
    # PROCESSING
    # Reading file 
    BYTES_PER_PIXEL = 4 #RGBA
    data = bytearray( MAGICK_NUMBER )
    size_data = os.path.getsize( args.file )
    with open(args.file, 'rb') as file_in:
        data = data + size_data.to_bytes(4,byteorder='little') + bytearray( file_in.read() )
    # Padding the data
    dim_img = math.ceil( math.sqrt( len(data) / BYTES_PER_PIXEL ) )
    for i in range(dim_img*dim_img*BYTES_PER_PIXEL - len(data) ):
        data.append(0)
    # Interpreting as a raw image and saving
    size_img = ( dim_img, dim_img )
    img = Image.frombytes('RGBA', size_img, bytes(data) )
    # TODO : Test if output folder exists
    img.save(args.output)

# EXTRACTING
else:    
    raw = Image.open(args.file).tobytes()
    if raw[ 0:8 ] != MAGICK_NUMBER:
        print("This is not a PNGized image!")
        exit(-1)
    size = int.from_bytes( raw[ 8:12 ], byteorder='little' )
    with open(args.output,"wb") as file_out:
        file_out.write( raw[ 12:12+size ] )
