from pychee6 import LycheeClient
from termcolor import colored
from pathlib import Path
from concurrent.futures import as_completed
from context_menu import menus
from tqdm import tqdm
import argparse
import os
import sys
import json

# 这个类用来封装一些常用操作
class lychee_cli:
    def __init__(self, host:str, verbose:bool, max_thread):
        self.client = LycheeClient(host, verbose, max_thread)
        self.verbose = verbose

    def login(self, token:str=None, username:str=None, password:str=None):
        ret = True

        if token:
            ret = self.client.login_by_token(token)
        elif username and password:
            ret, err = self.client.login_by_passwd(username, password)
            if not ret:
                print (err)
        
        return ret

    # 需要判断是路径还是id    
    def list_album(self, album_id:str, only_album=False):
        if album_id == "/":
            res = self.client.get_albums()
            if "message" in res.keys():
                print (res)
                return 
            print (f"--------- {colored("root", "cyan")} ")
            # print (json.dumps(res, ensure_ascii=False))
            for album in res["albums"]:
                print (colored(f"+ {album["title"]}\t{album["id"]}\t{album["created_at"]}", "blue"))

            for album in res["shared_albums"]:  # 有时相册会出现在这里
                print (colored(f"+ {album["title"]}\t{album["id"]}\t{album["created_at"]}", "blue"))

            if not only_album:
                res = self.client.get_album("unsorted")
                for photo in res["resource"]["photos"]:
                    print (colored(f"  {photo["title"]}\t{photo["id"]}\t{photo["created_at"]}", "green"))
        else:
            res = self.client.get_album(album_id)
            if "message" in res.keys():
                print (res)
                return 
            id = res["resource"]["id"]
            # title = res["resource"]["title"]
            cur_path = self.client.album_id2path(album_id)
            print (f"--------- {colored(cur_path, "cyan")} [{id}]")
            for album in res["resource"]["albums"]:
                print (colored(f"+ {album["title"]}\t{album["id"]}\t{album["created_at"]}", "blue"))
            
            if not only_album:
                for photo in res["resource"]["photos"]:
                    print (colored(f"  {photo["title"]}\t{photo["id"]}\t{photo["created_at"]}", "green"))
    
    def wait_task(self):
        try:
            futures = self.client.threadpool_get_futures()
            with tqdm(total=len(futures)) as pbar:
                for i, future in enumerate(as_completed(futures)):
                    result = future.result()
                    if result.get("message", None) != None:
                        print(f"{colored(str(result), "red")}")
                    pbar.update(1)
        except KeyboardInterrupt:
            futures = self.client.threadpool_get_futures()
            for future in futures:
                if not future.running():
                    future.cancel()
        except Exception as e:
            raise e

    def upload_album(self, album_id, files_path, skip_exist_photo=False):
        # print (f"upload_album {album_id} {files_path} {skip_exist_photo}")
        files_path = os.path.abspath(files_path)
        if os.path.isdir(files_path):
            base_name = Path(files_path).name
            parent_album_id = ""

            if album_id in ["/", "", None]:
                res = self.client.get_albums()
                for album in res["albums"]:
                    if base_name == album["title"]:
                        parent_album_id = album["id"]
            elif album_id != "":
                res = self.client.get_album(album_id)
                for album in res["resource"]["albums"]:
                    if base_name == album["title"]:
                        parent_album_id = album["id"]
            
            if parent_album_id == "":
                parent_album_id = self.client.create_album(base_name, album_id)

            self.client.upload_album(parent_album_id, files_path, skip_exist_photo)
            self.wait_task()
        else:
            print (f"{files_path} 不是一个合法的目录或者它不存在")

    
    def upload_photo(self, album:str, file_path:str):
        if os.path.isfile(file_path):
            print (self.client.upload_photo(album, file_path))
    
    def download_album(self, album_id:str, save_path:str):
        os.makedirs(save_path, exist_ok=True)
        if album_id in ["/", ""]:
            downloaded_title = []
            for album in self.client.get_albums()["albums"]:
                album_id = album["id"]
                album_title = album["title"]
                if album_title in downloaded_title:
                    album_title += f".[{album["id"]}]"
                else:
                    downloaded_title.append(album_title)
                self.client.download_album(album["id"], os.path.join(save_path, album_title))
            self.client.download_album("unsorted", save_path)
        else:
            self.client.download_album(album_id, save_path)
        
        self.wait_task()
    
    def create_album(self, album_name:str, album_id:str):
        return self.client.create_album(album_name, album_id)

    def delete_album(self, album_id:str):
        return self.client.delete_albums([album_id])

    def conv_album_id(self, album_id):
        if album_id[0] == "/":
            print (self.client.album_path2id(album_id))
        else:
            res = self.client.album_id2path(album_id)
            if len(res): 
                print (res)
            else: 
                print (f"找不到 {album_id} 对应的相册")
    
    def reg_context(self):
        try:
            self.unreg_context()
        except:
            pass
        # python_path = sys.executable
        root = menus.ContextMenu('Upload to Lychee', type='FILES')
        root.add_items([
                menus.ContextCommand('✨刷新(如果相册有修改)', command=f"? -m pychee6.cli reg_context", command_vars=["PYTHONLOC"]),
                menus.ContextCommand('❌取消注册', command=f"? -m pychee6.cli unreg_context", command_vars=["PYTHONLOC"]),
                menus.ContextCommand('🔻上传到此处', command=f"? -m pychee6.cli u_p / ?", command_vars=["PYTHONLOC",'FILENAME']),
            ])
        
        def get_items(parent, album_id):
            res = self.client.get_album(album_id)
            for album in res["resource"]["albums"]:
                tmp = menus.ContextMenu(album["title"])
                tmp.add_items([
                    menus.ContextCommand(f'🔻上传到此处', command=f"? -m pychee6.cli u_p -- {album['id']} ?", command_vars=["PYTHONLOC",'FILENAME'])
                ])
                get_items(tmp, album["id"])
                parent.add_items([tmp])
                print (album["title"], len(parent.sub_items))

        res = self.client.get_albums()
        for album in res["albums"]:
            tmp = menus.ContextMenu(album["title"])
            tmp.add_items([
                menus.ContextCommand(f'🔻上传到此处', command=f"? -m pychee6.cli u_p -- {album['id']} ?", command_vars=["PYTHONLOC",'FILENAME'])
            ])
            get_items(tmp, album["id"])
            root.add_items([tmp])
            print (album["title"], len(root.sub_items))

        def display_menu(menu):
            print(f"Menu: {menu.name}")
            for item in menu.sub_items:
                if isinstance(item, menus.ContextMenu):
                    display_menu(item)
                else:
                    print(f"  - {item.name} (Command: {item.command})")

        display_menu(root)
        root.compile()
    
    def unreg_context(self):
        menus.removeMenu("Upload to Lychee", type='FILES')

def main():
    parser = argparse.ArgumentParser(description="这是LycheeClient的cli版本，你可以把这个当作库的使用示例。\n大多数情况下，你可以使用album_id或者相册路径为参数。\n\talbum_id是一个24位长度的字符串形如：b4noPnuHQSSCXZL_IMsLEGAJ。\n\t相册路径是以/开头的字符串形如：/deepth_1/deepth_2。其中单独的/表示根目录或者说未分类", formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-t", "--token", help="登录所需要的api token，与用户名二选一 可以通过 LYCHEE_TOKEN 环境变量提供")
    parser.add_argument("-u", "--user", help="用户名 可以通过环境变量 LYCHEE_USERNAME 提供")
    parser.add_argument("-p", "--passwd", help="密码 可以通过环境变量 LYCHEE_PASSWORD 提供")
    parser.add_argument("-H", "--host", help="服务器地址，形如: http://exp.com:8808/ 可以通过环境变量 LYCHEE_HOST 提供")
    parser.add_argument("-m", "--max_thread", default=5, help="线程池大小 影响上传下载数量，默认为5")
    parser.add_argument("-v", "--verbose", action='store_true', help="输出调试信息")

    subargs = parser.add_subparsers(dest='command')

    upload_album_arg = subargs.add_parser("upload_album", aliases=["u_a"], help="上传相册，album_id为'/'则上传到根相册")
    upload_album_arg.add_argument("album_id", help="相册id，可以为'/'开头的相册路径")
    upload_album_arg.add_argument("path", help="需要上传的目录")
    upload_album_arg.add_argument("--skip_exist_photo", action='store_true', help="根据标题名跳过已经存在的图片")

    upload_photo_arg = subargs.add_parser("upload_photo", aliases=["u_p"], help="上传图片到相册，album_id为'/'则上传到未分类")
    upload_photo_arg.add_argument("album_id", help="相册id，可以为'/'开头的相册路径")
    upload_photo_arg.add_argument("path", help="需要上传的图片")

    download_album_arg = subargs.add_parser("download_album", aliases=["d_a"], help="下载相册，album_id为'/'则下载所有")
    download_album_arg.add_argument("album_id", help="相册id，可以为'/'开头的相册路径")
    download_album_arg.add_argument("path", help="下载的目标目录")

    create_album_arg = subargs.add_parser("create_album", aliases=["c_a"], help="创建相册，album_id为'/'则在根相册创建")
    create_album_arg.add_argument("album_id", help="父相册id，可以为'/'开头的相册路径")
    create_album_arg.add_argument("album_name", help="新相册的名字")

    delete_album_arg = subargs.add_parser("delete_album", aliases=["del_a"], help="删除指定相册")
    delete_album_arg.add_argument("album_id", help="需要删除的相册id")

    list_arg = subargs.add_parser("list", aliases=["ls"], prog="list <dist> <album_id/album_path>", help="列出相册和图片")
    list_arg.add_argument("target", nargs="?", default="/", help="可以是相册id或者'/'开头的相册路径，如果以'-'开头，则需要在前面补充--，形如list -- -iw78289")

    list_arg = subargs.add_parser("list_album", aliases=["la"], prog="list_album <dist> <album_id/album_path>", help="仅显示相册")
    list_arg.add_argument("target", nargs="?", default="/", help="可以是相册id或者'/'开头的相册路径，如果以'-'开头，则需要在前面补充--list_album -- -iw78289")

    conv_arg = subargs.add_parser("conv", aliases=["c_v"], help="album_id和album_path互相转换")
    conv_arg.add_argument("album_id", help="album_id 和 album_path 相互转换，相册路径需以'/'开头")

    reg_context_arg = subargs.add_parser("reg_context", help="将上传下载功能注册到鼠标上下文菜单中")
    unreg_context_arg = subargs.add_parser("unreg_context", help="取消注册鼠标上下文菜单中的上传下载功能")

    args = parser.parse_args()
    # print (args)

    if args.command in ["help", "h"]:
        parser.print_help()
        return 

    lychee_host = args.host
    if not lychee_host:
        lychee_host = os.getenv("LYCHEE_HOST")
    
    lychee_token = args.token
    lychee_username = args.user
    lychee_password = args.passwd

    # print (os.environ)

    if lychee_token==None and lychee_username==None and lychee_password==None:
        lychee_token = os.getenv("LYCHEE_TOKEN")
        lychee_username = os.getenv("LYCHEE_USERNAME")
        lychee_password = os.getenv("LYCHEE_PASSWORD")

    if lychee_token==None and lychee_username==None and lychee_password==None:
        print ("需要提供登录信息，可以指定 user和passwd参数，或者通过环境变量提供（见帮助信息）")
        parser.print_help()
        return 
    
    cli = lychee_cli(lychee_host, args.verbose, int(args.max_thread))
    if not cli.login(lychee_token, lychee_username, lychee_password):
        return

    if args.command in ["list", "ls"]:
        cli.list_album(args.target)
    elif args.command in ["list_album", "la"]:
        cli.list_album(args.target, True)
    elif args.command in ["upload_album", "u_a"]:
        cli.upload_album(args.album_id, args.path, args.skip_exist_photo)
    elif args.command in ["upload_photo", "u_p"]:
        cli.upload_photo(args.album_id, args.path)
    elif args.command in ["download_album", "d_a"]:
        cli.download_album(args.album_id, args.path)
    elif args.command in ["create_album", "c_a"]:
        new_album_id = cli.create_album(args.album_name, args.album_id)
        print (f"新相册id: {new_album_id}")
    elif args.command in ["delete_album", "del_a"]:
        print (cli.delete_album(args.album_id))
    elif args.command in ["conv", "c_v"]:
        if args.album_id:
            cli.conv_album_id(args.album_id)
    elif args.command in ["reg_context"]:
        cli.reg_context()
    elif args.command in ["unreg_context"]:
        cli.unreg_context()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()