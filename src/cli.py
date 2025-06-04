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
import gettext
import locale

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
                parent_album_id = self.client.create_album(album_id, base_name)

            self.client.upload_album(parent_album_id, files_path, skip_exist_photo)
            self.wait_task()
        else:
            print (_("'{path}' is not a valid directory or it does not exist").format(path=files_path))

    
    def upload_photo(self, album:str, file_path:str):
        if os.path.isfile(file_path):
            print (self.client.upload_photo(album, file_path))
    
    def download_album(self, album:str, save_path:str):
        if album in ["/", ""]:
            downloaded_title = []
            save_path = os.path.join(save_path,"lychee_root")
            os.makedirs(save_path, exist_ok=True)
            res = self.client.get_albums()
            all_albums = res["albums"] + res["shared_albums"]
            for album in all_albums:
                album_id = album["id"]
                album_title = album["title"]
                if album_title in downloaded_title:
                    album_title += f".[{album_id}]"
                else:
                    downloaded_title.append(album_title)
                self.client.download_album(album_id, os.path.join(save_path, album_title))
            self.client.download_album("unsorted", save_path)
        else:

            if album[0] == "/":
                album_title = album.split("/")[-1]
            else:
                album_title = self.client.get_album(album)["resource"]["title"]
            save_path = os.path.join(save_path, album_title)

            self.client.download_album(album, save_path)
        
        self.wait_task()
    
    def create_album(self, album:str, album_name:str):
        return self.client.create_album(album, album_name)

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
                print (_("Cannot find album for ID: {id}").format(id=album_id))
    
    def reg_context(self):
        try:
            self.unreg_context()
        except:
            pass
        # python_path = sys.executable
        root = menus.ContextMenu(_('Upload to Lychee'), type='FILES')
        root.add_items([
                menus.ContextCommand(_('✨Refresh (if album modified)'), command=f"? -m pychee6.cli reg_context", command_vars=["PYTHONLOC"]),
                menus.ContextCommand(_('❌Unregister'), command=f"? -m pychee6.cli unreg_context", command_vars=["PYTHONLOC"]),
                menus.ContextCommand(_('🔻Upload here'), command=f"? -m pychee6.cli u_p / ?", command_vars=["PYTHONLOC",'FILENAME']),
            ])
        
        def get_items(parent, album_id):
            res = self.client.get_album(album_id)
            for album in res["resource"]["albums"]:
                tmp = menus.ContextMenu(album["title"])
                tmp.add_items([
                    menus.ContextCommand(f'🔻Upload to here', command=f"? -m pychee6.cli u_p -- {album['id']} ?", command_vars=["PYTHONLOC",'FILENAME'])
                ])
                get_items(tmp, album["id"])
                parent.add_items([tmp])
                print (album["title"], len(parent.sub_items))

        res = self.client.get_albums()
        for album in res["albums"]:
            tmp = menus.ContextMenu(album["title"])
            tmp.add_items([
                menus.ContextCommand(f'🔻Upload to here', command=f"? -m pychee6.cli u_p -- {album['id']} ?", command_vars=["PYTHONLOC",'FILENAME'])
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
    # Initialize internationalization
    _ = gettext.gettext
    try:
        loc = locale.getdefaultlocale()
        if not loc[0] == "en_US":
            current_dir = os.path.dirname(os.path.abspath(__file__))
            localedir = os.path.join(current_dir, 'locales')
            l10n = gettext.translation(loc[0], localedir=localedir, languages=[loc[0]])
            l10n.install()
            _ = l10n.gettext
    except Exception as e:
        print(f"{e}\nUsing default language - English(en_US.UTF-8)")

    parser = argparse.ArgumentParser(description=_(
        "This is the CLI version of LycheeClient, which can be used as an example of library usage.\n"
        "In most cases, you can use album_id or album path as parameters.\n"
        "\talbum_id is a 24-character string like: b4noPnuHQSSCXZL_IMsLEGAJ\n"
        "\tAlbum path starts with / like: /depth_1/depth_2. Single / represents root directory or unsorted\n"
        "\tFor issues or suggestions, please create an issue at: https://github.com/x1ntt/pychee6 😉"
    ), formatter_class=argparse.RawDescriptionHelpFormatter)
    
    parser.add_argument("-t", "--token", help=_("API token required for login, alternative to username. Can be provided via LYCHEE_TOKEN environment variable"))
    parser.add_argument("-u", "--user", help=_("Username. Can be provided via LYCHEE_USERNAME environment variable"))
    parser.add_argument("-p", "--passwd", help=_("Password. Can be provided via LYCHEE_PASSWORD environment variable"))
    parser.add_argument("-H", "--host", help=_("Server address, like: http://exp.com:8808/. Can be provided via LYCHEE_HOST environment variable"))
    parser.add_argument("-m", "--max_thread", default=5, help=_("Thread pool size affecting upload/download count, default is 5"))
    parser.add_argument("-v", "--verbose", action='store_true', help=_("Output debug information"))

    subargs = parser.add_subparsers(dest='command')

    upload_album_arg = subargs.add_parser("upload_album", aliases=["u_a"], 
        help=_("Upload album, album_id as '/' then upload to root album"))
    upload_album_arg.add_argument("album_id", 
        help=_("Album id, can be '/' leading album path"))
    upload_album_arg.add_argument("path", 
        help=_("Path to upload directory"))
    upload_album_arg.add_argument("--skip_exist_photo", action='store_true', 
        help=_("Based on title name skip existing photos"))

    upload_photo_arg = subargs.add_parser("upload_photo", aliases=["u_p"], 
        help=_("Upload photo to album, album_id as '/' then upload to unsorted"))
    upload_photo_arg.add_argument("album_id", 
        help=_("Album id, can be '/' leading album path"))
    upload_photo_arg.add_argument("path", 
        help=_("Path to upload photo"))

    download_album_arg = subargs.add_parser("download_album", aliases=["d_a"], 
        help=_("Download album, album_id as '/' then download all"))
    download_album_arg.add_argument("album_id", 
        help=_("Album id, can be '/' leading album path"))
    download_album_arg.add_argument("path", 
        help=_("Download target directory"))

    create_album_arg = subargs.add_parser("create_album", aliases=["c_a"], 
        help=_("Create album, album_id as '/' then create album in root"))
    create_album_arg.add_argument("album_id", 
        help=_("Parent album id, can be '/' leading album path"))
    create_album_arg.add_argument("album_name", 
        help=_("New album name"))

    delete_album_arg = subargs.add_parser("delete_album", aliases=["del_a"], 
        help=_("Delete specified album"))
    delete_album_arg.add_argument("album_id", 
        help=_("Album id to delete"))

    list_arg = subargs.add_parser("list", aliases=["ls"], 
        prog="list <dist> <album_id/album_path>", 
        help=_("List album and photos"))
    list_arg.add_argument("target", nargs="?", default="/", 
        help=_("Can be album id or '/' leading album path, if it starts with '-', then need to add '--', like list -- -iw78289"))

    list_arg = subargs.add_parser("list_album", aliases=["la"], 
        prog="list_album <dist> <album_id/album_path>", 
        help=_("Only display albums"))
    list_arg.add_argument("target", nargs="?", default="/", 
        help=_("Can be album id or '/' leading album path, if it starts with '-', then need to add '--list_album -- -iw78289"))

    conv_arg = subargs.add_parser("conv", aliases=["c_v"], 
        help=_("album_id and album_path switch"))
    conv_arg.add_argument("album_id", 
        help=_("album_id and album_path switch, album path starts with '/'"))

    reg_context_arg = subargs.add_parser("reg_context", 
        help=_("Register upload/download function to mouse context menu"))
    unreg_context_arg = subargs.add_parser("unreg_context", 
        help=_("Unregister mouse context menu"))

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
        print (_("Need provide login information, can specify user and passwd parameters, or provide via environment variables (see help)"))
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
        new_album_id = cli.create_album(args.album_id, args.album_name)
        print (_("New album id: {id}").format(id=new_album_id))
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