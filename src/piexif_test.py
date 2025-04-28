from PIL import Image
import xml.etree.ElementTree as ET
import piexif
import sys


def remove_xmp_title(xml_data):
    # 解析 XML
    root = ET.fromstring(xml_data)

    # 定义命名空间
    namespaces = {
        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        'dc': 'http://purl.org/dc/elements/1.1/'
    }

    # 查找并删除 <dc:title> 和 <dc:description> 元素
    for description in root.findall('.//rdf:Description', namespaces):
        title_element = description.find('dc:title', namespaces)
        if title_element is not None:
            description.remove(title_element)

        description_element = description.find('dc:description', namespaces)
        if description_element is not None:
            description.remove(description_element)
    return ET.tostring(root, encoding='unicode')
    
im = Image.open(sys.argv[1])
exif_dict = piexif.load(im.info["exif"])


print (type(exif_dict), exif_dict["0th"][piexif.ImageIFD.ImageDescription].decode("utf8"))
print (type(exif_dict["0th"][piexif.ImageIFD.XPTitle]), bytes(exif_dict["0th"][piexif.ImageIFD.XPTitle]).decode("utf-16"))

del exif_dict["0th"][piexif.ImageIFD.ImageDescription]
del exif_dict["0th"][piexif.ImageIFD.XPTitle]

print (exif_dict)

xmp = remove_xmp_title(im.info["xmp"].decode("utf8"))

print (xmp)

im.info["xmp"] = xmp.encode("utf8")

print (im.info["xmp"])

im.save(f"c_{sys.argv[1]}", exif=piexif.dump(exif_dict))