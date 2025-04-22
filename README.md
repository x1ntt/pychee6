
这是个对`lychee6`的`v2 api`进行包装的库，并提供一些实用功能。同时提供了一个简单命令行客户端，如果要二次开发，可以参考`lychee-cli.py`

> 需要注意，目前仅支持`lychee6`以上的版本

库目前缺少一些细节功能，如果有什么急需的功能，请提issue，如果我有时间，我会尽快实现

# 安装

## 通过pip3

```shell
pip3 install git+https://github.com/x1ntt/pychee6
```

## 手动

```shell
git clone https://github.com/x1ntt/pychee6.git
cd pychee6
pip3 install .
```

对于库的所有接口，请参考`src/pychee6.py`文件中的`LycheeClient`接口注释

# 文档

`pip3 install pdoc`安装`pdoc`

然后你可以通过 `pdoc pychee6.py`的方式生成文档，详细见[pdoc](https://pdoc.dev/docs/pdoc.html)

# 一些cli使用例子

安装完毕后可以通过`python3 -m pychee6.lychee-cli`来使用`cli`

```shell
python3 -m pychee6.lychee-cli -h
usage: lychee-cli.py [-h] [-t TOKEN] [-u USER] [-p PASSWD] [-H HOST]
                     {upload_album,u_a,upload_photo,u_p,download_album,d_a,create_album,c_a,list,ls,list_album,la,conv,c_v} ...

这是LycheeClient的cli版本，你可以把这个当作库的使用示例。
大多数情况下，你可以使用album_id或者相册路径为参数。
        album_id是一个24位长度的字符串形如：b4noPnuHQSSCXZL_IMsLEGAJ。
        相册路径是以/开头的字符串形如：/deepth_1/deepth_2。其中单独的/表示根目录或者说未分类

positional arguments:
  {upload_album,u_a,upload_photo,u_p,download_album,d_a,create_album,c_a,list,ls,list_album,la,conv,c_v}
    upload_album (u_a)  自动创建相册，album_id为'/'则上传到根相册
    upload_photo (u_p)  上传图片到相册，album_id为'/'则上传到未分类
    download_album (d_a)
                        下载相册，album_id为'/'则下载所有
    create_album (c_a)  创建相册，album_id为'/'则在根相册创建
    list (ls)           列出相册和图片
    list_album (la)     仅显示相册
    conv (c_v)          album_id和album_path互相转换

options:
  -h, --help            show this help message and exit
  -t TOKEN, --token TOKEN
                        登录所需要的api token，与用户名二选一 可以通过 LYCHEE_TOKEN 环境变量提供
  -u USER, --user USER  用户名 可以通过环境变量 LYCHEE_USERNAME 提供
  -p PASSWD, --passwd PASSWD
                        密码 可以通过环境变量 LYCHEE_PASSWORD 提供
  -H HOST, --host HOST  服务器地址，形如: http://exp.com:8808/ 可以通过环境变量 LYCHEE_HOST 提供
```

## 登录
有两种提供登录信息的方法，可以通过参数提供，例如
```shell
# 通过 user 和 passwd 登录
lychee-cli.py --user admin --passwd admin --host http://127.0.0.1:3000/ ls
# 或短参数
python3 -m pychee6.lychee-cli -u root -p 123456 -H http://127.0.0.1:8802/ ls

# 通过 token 登录
lychee-cli.py --token xxxxxxxxxxxxx -H http://127.0.0.1:8802/
```
或者通过环境变量登录，user对应LYCHEE_USERNAME变量，passwd对应LYCHEE_PASSWORD变量，host对应LYCHEE_HOST变量,token对应LYCHEE_TOKEN变量

参数优先级更高，考虑到密码安全，建议使用token的方式登录，为了方便，建议设定环境变量`LYCHEE_HOST`和`LYCHEE_TOKEN`。以下例子均以环境变量为例，所以隐去登录相关参数

## 相关操作

+ 查看相册和照片列表
```shell
python3 -m pychee6.lychee-cli ls
```

+ 仅查看相册
```shell
python3 -m pychee6.lychee-cli la
```

+ 创建相册
```shell
python3 -m pychee6.lychee-cli c_a / new_album
python3 -m pychee6.lychee-cli c_a /new_album deepth_1
python3 -m pychee6.lychee-cli c_a p92kvXqyZUC6M-8CcPAwnCpd deepth_2

结果如下：
$ python3 -m pychee6.lychee-cli c_a / new_album
创建相册: new_album, /
新相册id: WdgpHuHV0MRQjtUBBMgh8DbS
$ python3 -m pychee6.lychee-cli c_a /new_album deepth_1
路径(/new_album)自动转换为id WdgpHuHV0MRQjtUBBMgh8DbS
创建相册: deepth_1, WdgpHuHV0MRQjtUBBMgh8DbS
新相册id: p92kvXqyZUC6M-8CcPAwnCpd
$ python3 -m pychee6.lychee-cli c_a p92kvXqyZUC6M-8CcPAwnCpd deepth_2
创建相册: deepth_2, p92kvXqyZUC6M-8CcPAwnCpd
新相册id: IrpwfQHM62h8_d-VDBu6YBps
```

+ 下载相册
```shell
python3 -m pychee6.lychee-cli d_a / ./tmp/
# 或指定id
python3 -m pychee6.lychee-cli d_a p92kvXqyZUC6M-8CcPAwnCpd ./tmp/
```

+ 上传相册
```shell
python3 -m pychee6.lychee-cli u_a /new_album ./tmp/test__album/
# 或指定id
python3 -m pychee6.lychee-cli u_a p92kvXqyZUC6M-8CcPAwnCpd ./tmp/test__album/
```

+ 上传图片
```shell
python3 -m pychee6.lychee-cli u_p /new_album ./tmp/test__album/157_modify.webp
```

+ 相册id和相册路径互相转换
```shell
python3 -m pychee6.lychee-cli c_v /new_album 
python3 -m pychee6.lychee-cli c_v p92kvXqyZUC6M-8CcPAwnCpd
```


# 目前已知问题

+ 使用`--skip_exist`选项时，如果相册中已存在的文件和本地待上传文件名不相同，则会重复上传，并且新上传的相册标题时本来存在的文件名。这意味着，如果你首次上传目录后改变其中某个图片的标题，那么之后每次重复上传这个目录时这个文件都会再上传一次。

# TODO：

- [x] 跳过已存在文件上传
- [x] 分段上传以解决大文件上传问题
- [ ] 上传目录时，如果发现cover命名的文件直接设置为封面
- [x] 考虑下载的时候修复后缀？以解决修改相册名后丢失文件后缀的问题
- [x] Ctrl+C 安全关闭多线程
- [x] 合理的错误传递，{'message': 'File format not supported', 'exception': 'MediaFileUnsupportedException'}
- [ ] 图片标题抹除工具
- [ ] ~~部分图片上传title变为Photo，并且title有被截断的现象（如果图片信息中包含标题，lychee优先使用标题信息作为标题从而忽略文件名，如果有需要可以上传之前抹除图片标题信息）~~