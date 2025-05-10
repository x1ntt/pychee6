import sys
import os
import pyexiv2
import shutil
import logging

orin_pwd = os.getcwd()

# print (img.read_exif())
# print (img.read_iptc())
# print (img.read_xmp())

def remove_title(file_name, sub_path): # 如果文件有只读属性，建议提供第二个参数不修改原文件
    with open(file_name, ['rb','rb+'][sub_path=='']) as f:
        target_file = os.path.join(orin_pwd, sub_path, file_name)

        try:
            with pyexiv2.ImageData(f.read()) as img:
                if len(img.read_exif())!=0 or len(img.read_xmp())!=0 or len(img.read_iptc())!=0:
                    img.modify_exif({"Exif.Image.ImageDescription":None,"Exif.Image.XPTitle":None})
                    img.modify_xmp({"Xmp.dc.title":None,"Xmp.dc.description":None})
                    img.modify_iptc({"Iptc.Application2.BylineTitle":None,"Iptc.Application2.Caption":None})
                    if sub_path == '':
                        f.seek(0)
                        f.truncate()
                        f.write(img.get_bytes())
                    else:
                        with open(target_file, 'wb') as f2:
                            f2.write(img.get_bytes())
                else:
                    print (f"{file_name} 没有元数据，直接复制", (orin_pwd, sub_path, file_name),img.read_exif(),img.read_iptc(),img.read_xmp())
                    shutil.copy(file_name, target_file)
        except Exception as e:
            print (f"{file_name} 处理错误: {str(e)}")
            logging.exception(e)
            shutil.copy(file_name, target_file)

if len(sys.argv) == 3:
    src = sys.argv[1]
    sub_path = sys.argv[2]
    if sub_path == '-':
        sub_path = ''
    if os.path.isfile(src):
        src_path = os.path.split(src)[0]
        if src_path != "":
            os.chdir(src_path)
        os.makedirs(os.path.join(orin_pwd, sub_path), exist_ok=True)
        remove_title(os.path.split(src)[1], sub_path)
    elif os.path.isdir(src):
        os.chdir(src)
        count = 0
        for dirpath, dirnames, filenames in os.walk('.'):
            os.makedirs(os.path.join(orin_pwd, sub_path, dirpath), exist_ok=True)
            for filename in filenames:
                tmp_filename = os.path.join(dirpath,filename)
                count+=1
                print(f"文件：{tmp_filename}, {count}")

                remove_title(tmp_filename, sub_path)
else:
    print (f"用来删除图片的标题和描述信息\n {sys.argv[0]} <src file/path> <dst path>; \n dst 为-时直接修改原文件")