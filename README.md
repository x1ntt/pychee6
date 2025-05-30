
[English version below](#english) <-- Click

这是对`lychee6`的`v2 api`进行包装的库，并提供一些实用功能。同时提供了一个简单命令行客户端`lychee-cli.py`，如果要使用`pychee6`，可以参考它

> 需要注意，目前仅支持`lychee6`以上的版本

如果有问题或者急需的功能，请提issue，如果我有时间，我会尽快实现
If you have any questions or urgently needed features, please raise an issue. If I have time, I will implement it as soon as possible.

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

# 关于cli

安装完毕后可以通过`python3 -m pychee6.cli`来使用`cli`

如果在windows设备上，需要使用`python`命令而非`python3`

```shell
python -m pychee6.cli -h
usage: cli.py [-h] [-t TOKEN] [-u USER] [-p PASSWD] [-H HOST] [-m MAX_THREAD] [-v]
              {upload_album,u_a,upload_photo,u_p,download_album,d_a,create_album,c_a,delete_album,del_a,list,ls,list_album,la,conv,c_v,reg_context,unreg_context} ...

这是LycheeClient的cli版本，你可以把这个当作库的使用示例。
大多数情况下，你可以使用album_id或者相册路径为参数。
        album_id是一个24位长度的字符串形如：b4noPnuHQSSCXZL_IMsLEGAJ。
        相册路径是以/开头的字符串形如：/deepth_1/deepth_2。其中单独的/表示根目录或者说未分类

positional arguments:
  {upload_album,u_a,upload_photo,u_p,download_album,d_a,create_album,c_a,delete_album,del_a,list,ls,list_album,la,conv,c_v,reg_context,unreg_context}
    upload_album (u_a)  上传相册，album_id为'/'则上传到根相册
    upload_photo (u_p)  上传图片到相册，album_id为'/'则上传到未分类
    download_album (d_a)
                        下载相册，album_id为'/'则下载所有
    create_album (c_a)  创建相册，album_id为'/'则在根相册创建
    delete_album (del_a)
                        删除指定相册
    list (ls)           列出相册和图片
    list_album (la)     仅显示相册
    conv (c_v)          album_id和album_path互相转换
    reg_context         将上传下载功能注册到鼠标上下文菜单中
    unreg_context       取消注册鼠标上下文菜单中的上传下载功能

options:
  -h, --help            show this help message and exit
  -t, --token TOKEN     登录所需要的api token，与用户名二选一 可以通过 LYCHEE_TOKEN 环境变量提供
  -u, --user USER       用户名 可以通过环境变量 LYCHEE_USERNAME 提供
  -p, --passwd PASSWD   密码 可以通过环境变量 LYCHEE_PASSWORD 提供
  -H, --host HOST       服务器地址，形如: http://exp.com:8808/ 可以通过环境变量 LYCHEE_HOST 提供
  -m, --max_thread MAX_THREAD
                        线程池大小 影响上传下载数量，默认为5
  -v, --verbose         输出调试信息
```

## 登录
有两种提供登录信息的方法，可以通过参数提供，例如
```shell
# 通过 user 和 passwd 登录
python3 -m pychee6.cli --user admin --passwd admin --host http://127.0.0.1:3000/ ls
# 或短参数
python3 -m pychee6.cli -u root -p 123456 -H http://127.0.0.1:8802/ ls

# 通过 token 登录
lychee-cli.py --token xxxxxxxxxxxxx -H http://127.0.0.1:8802/
```

可以通过环境变量提供登录信息，例如

|命令行参数|环境变量|含义|
|-|-|-|
|-u|LYCHEE_USERNAME|用户名|
|-p|LYCHEE_PASSWORD|密码|
|-t|LYCHEE_TOKEN|API token，会优先采用|

命令行参数优先级更高。方便起见，建议设定环境变量`LYCHEE_HOST`和`LYCHEE_TOKEN`以使用`cli`

以下例子设置了环境变量，所以隐去登录相关参数

## 相关操作

查看相册和照片列表，缩写和全称对应关系见上方帮助信息
```shell
python3 -m pychee6.cli ls   # 列出相册和图片
python3 -m pychee6.cli la   # 列出相册
python3 -m pychee6.cli c_a / new_album # 在根目录创建名为`new_album`的相册
python3 -m pychee6.cli c_a /new_album deepth_1  # 在`new_album`下创建名为`deepth_2`的相册
python3 -m pychee6.cli d_a / ./tmp/     # 下载根目录下的相册到`./tmp/`
python3 -m pychee6.cli u_a /new_album ./tmp/test__album/ #  上传`./tmp/test__album/`目录到`/new_album`
python3 -m pychee6.cli u_p /new_album ./tmp/test__album/157_modify.webp # 上传图片

# 相册id和相册路径互相转换
python3 -m pychee6.cli c_v /new_album 
python3 -m pychee6.cli c_v p92kvXqyZUC6M-8CcPAwnCpd
```

> 以上命令行参数中，可以使用`album_id`或`album_path`，使用`album_id`将会更快。`album_path`为`/`开头的相册路径，例如`/depth_1/depth_2`，`/`为根目录


## 将上传下载功能注册到资源管理的上下文菜单

### 对于windows

详见这里：[x1ntt/pychee6_cm](https://github.com/x1ntt/pychee6_cm)

```shell
python3 -m pychee6_cm --register   # 注册
python3 -m pychee6_cm --unregister # 取消注册
```

### 对于linux
我并未完整实现该功能，如果有需要请提issue🫡，你可以通过下面的指令测试是否可以正常添加上下文菜单

```shell
python3 -m pychee6.cli reg_context    # 注册
python3 -m pychee6.cli unreg_context  # 取消注册
```
> `linux`上使用`https://github.com/saleguas/context_menu`库实现，该库目前仅支持`Nautilus`

# 汉化
```shell
xgettext -k_ -o locales/zh_CN/LC_MESSAGES/zh_CN.po cli.py
msgfmt -o locales/zh_CN/LC_MESSAGES/zh_CN.mo locales/zh_CN/LC_MESSAGES/zh_CN.po
```

# english

# pychee6 - Lychee6 v2 API Wrapper Library and Command-Line Client

This is a library that wraps the `lychee6` `v2 api` and provides some useful functions. It also offers a simple command-line client `lychee-cli.py`. If you want to use `pychee6`, you can refer to it.

> Note that currently only versions above `lychee6` are supported.

If you have any questions or urgently needed features, please raise an issue. If I have time, I will implement it as soon as possible.

# Installation

## Via pip3

```shell
pip3 install git+https://github.com/x1ntt/pychee6
```

## Manual

```shell
git clone https://github.com/x1ntt/pychee6.git
cd pychee6
pip3 install .
```

For all library interfaces, please refer to the `LycheeClient` interface comments in the `src/pychee6.py` file.

# Documentation

```shell
pip3 install pdoc
```

Then you can generate documentation using `pdoc pychee6.py`. For more details, see [pdoc API documentation](https://pdoc.dev/docs/pdoc.html).

# About the CLI

After installation, you can use the `cli` by running `python3 -m pychee6.cli`.

If you are on a Windows device, use the `python` command instead of `python3`.

```shell
python -m pychee6.cli -h
usage: cli.py [-h] [-t TOKEN] [-u USER] [-p PASSWD] [-H HOST] [-m MAX_THREAD] [-v]
              {upload_album,u_a,upload_photo,u_p,download_album,d_a,create_album,c_a,delete_album,del_a,list,ls,list_album,la,conv,c_v,reg_context,unreg_context} ...

This is the CLI version of LycheeClient, which you can use as an example of how to use the library. In most cases, you can use album_id or album path as parameters.
        album_id is a 24-character string, such as b4noPnuHQSSCXZL_IMsLEGAJ.
        The album path is a string starting with /, such as /depth_1/depth_2. A single / represents the root directory or "unsorted" category.

positional arguments:
  {upload_album,u_a,upload_photo,u_p,download_album,d_a,create_album,c_a,delete_album,del_a,list,ls,list_album,la,conv,c_v,reg_context,unreg_context}
    upload_album (u_a): Upload an album. If album_id is /, upload to the root album.
    upload_photo (u_p): Upload photos to an album. If album_id is /, upload to the "unsorted" category.
    download_album (d_a): Download an album. If album_id is /, download everything.
    create_album (c_a): Create an album. If album_id is /, create in the root album.
    delete_album (del_a): Delete a specified album.
    list (ls): List albums and photos.
    list_album (la): Display albums only.
    conv (c_v): Convert between album_id and album_path.
    reg_context: Register upload and download functions to the context menu of the file manager.
    unreg_context: Unregister upload and download functions from the context menu of the file manager.

options:
  -h, --help            show this help message and exit
  -t, --token TOKEN     The API token required for login. Either this or the username is required. Can be provided via the LYCHEE_TOKEN environment variable.
  -u, --user USER       Username. Can be provided via the LYCHEE_USERNAME environment variable.
  -p, --passwd PASSWD   Password. Can be provided via the LYCHEE_PASSWORD environment variable.
  -H, --host HOST       Server address, such as http://exp.com:8808/. Can be provided via the LYCHEE_HOST environment variable.
  -m, --max_thread MAX_THREAD
                        The size of the thread pool, affecting the number of uploads/downloads. The default is 5.
  -v, --verbose         Output debug information.
```

## Login

There are two ways to provide login information, either through parameters or environment variables.

### Providing Login Information via Parameters

```shell
# Login with username and password
python3 -m pychee6.cli --user admin --passwd admin --host http://127.0.0.1:3000/ ls
# Or use short parameters
python3 -m pychee6.cli -u root -p 123456 -H http://127.0.0.1:8802/ ls

# Login with token
lychee-cli.py --token xxxxxxxxxxxxx -H http://127.0.0.1:8802/
```

### Providing Login Information via Environment Variables

| Command-Line Parameter | Environment Variable         | Meaning                     |
|:-----------------------|:-----------------------------|:----------------------------|
| `-u`                   | `LYCHEE_USERNAME`            | Username                    |
| `-p`                   | `LYCHEE_PASSWORD`            | Password                    |
| `-t`                   | `LYCHEE_TOKEN`               | API token, which takes precedence |

The command-line parameters have a higher priority. For convenience, it is recommended to set the environment variables `LYCHEE_HOST` and `LYCHEE_TOKEN` to use the `cli`. The following examples assume that the environment variables are set, so the login-related parameters are omitted.

## Operations

### Viewing Albums and Photos

The abbreviations and their corresponding full names can be found in the help information above.

```shell
python3 -m pychee6.cli ls   # List albums and photos
python3 -m pychee6.cli la   # List albums only
python3 -m pychee6.cli c_a / new_album # Create an album named `new_album` in the root directory
python3 -m pychee6.cli c_a /new_album deepth_1  # Create an album named `deepth_2` under `new_album`
python3 -m pychee6.cli d_a / ./tmp/     # Download the albums in the root directory to `./tmp/`
python3 -m pychee6.cli u_a /new_album ./tmp/test__album/ # Upload the directory `./tmp/test__album/` to `/new_album`
python3 -m pychee6.cli u_p /new_album ./tmp/test__album/157_modify.webp # Upload a photo

# Convert between album_id and album_path
python3 -m pychee6.cli c_v /new_album 
python3 -m pychee6.cli c_v p92kvXqyZUC6M-8CcPAwnCpd
```

> In the above command-line parameters, you can use `album_id` or `album_path`. Using `album_id` will be faster. `album_path` is a path starting with `/`, such as `/depth_1/depth_2`, where `/` represents the root directory.

## Registering Upload and Download Functions to the Context Menu of the File Manager

### For Windows

See here: [x1ntt/pychee6_cm](https://github.com/x1ntt/pychee6_cm)

```shell
python3 -m pychee6_cm --register   # Register
python3 -m pychee6_cm --unregister # Unregister
```

### For Linux

I have not fully implemented this feature. If you need it, please raise an issue🫡. You can use the following commands to test whether the context menu can be added normally:

```shell
python3 -m pychee6.cli reg_context    # Register
python3 -m pychee6.cli unreg_context  # Unregister
```

> The `linux` version uses the [context_menu](https://github.com/saleguas/context_menu) library, which currently only supports `Nautilus`.

# Translation
```shell
xgettext -k_ -o locales/zh_CN/LC_MESSAGES/zh_CN.po cli.py
msgfmt -o locales/zh_CN/LC_MESSAGES/zh_CN.mo locales/zh_CN/LC_MESSAGES/zh_CN.po
```