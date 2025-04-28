import sys

from pyexiv2 import Image

img = Image(sys.argv[1])
print ("123")
print (img)
print (img.read_exif())
print (img.read_iptc())
print (img.read_xmp())
img.close()