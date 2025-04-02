from requests import Session
from urllib.parse import unquote
from concurrent.futures import ThreadPoolExecutor, wait
import requests
import base64
import os
import math

class LycheeSession(Session):
    def __init__(self, base_url):
        super().__init__()
        # api v2
        self._base_url = base_url
        self._is_login = False
        self._api_version = "/api/v2/"
        self._header = {"Accept": "application/json", "Content-Type": "application/json"}

        super().request('GET', self._base_url)
        self._set_csrf_header()
    
    def _set_csrf_header(self):
        csrf_token = self.cookies.get("XSRF-TOKEN")
        if csrf_token is not None:
            if csrf_token != self._header.get("X-XSRF-TOKEN"):
                self._header["X-XSRF-TOKEN"] = unquote(
                    csrf_token
                ).replace('=', '')
    
    def request(self, method, url, *args, **kwargs):
        url = self._base_url + self._api_version + url
        self._set_csrf_header()

        # print (f"{method} {url}")

        if "headers" in kwargs:
            headers = self._header.copy()
            headers.update(kwargs["headers"])
        else:
            headers = self._header.copy()
        kwargs["headers"] = headers

        if "delete_headers" in kwargs:
            for del_head in kwargs["delete_headers"]:
                kwargs["headers"].pop(del_head, None)
            del kwargs["delete_headers"]

        response = super().request(method, url, *args, **kwargs)
        return response

class LycheeClient():
    """ 
    + `album_id`: The album id must be a string of 24 bytes in length. for example: `1NIXGEcGdYzLKgxxlNS8CdReX`
    + `album_path`: The album path must start with `/`. If there is only `/`, it means the root album
    """
    def __init__(self, base_url:str, max_workers:int=5):
        """ 
            :param base_url: Lychee API address 如 `http://127.0.0.1:5000/`
            :param max_workers: Maximum number of download threads
        """
        self._sess = LycheeSession(base_url)

        self._tasks_pool = ThreadPoolExecutor(max_workers=max_workers)
        self._futures = []
        self._file_name_list = []
    
    def wait_tasks(self):
        wait(self._futures)
        self._futures = []
    
    def threadpool_shutdown(self):
        self._tasks_pool.shutdown()
    
    def threadpool_get_futures(self):
        return self._futures

    def login_by_passwd(self, username:str, password:str):
        """ Log in with your account and password
        :param username: [required] username
        :param password: [required] password

        :return: `tuple`: (res:bool, reason:dict)
        """
        r = self._sess.post("Auth::login", json={
            "username": username, 
            "password": password
        })

        if r.status_code == 204:
            return True, {}
        return False, r.json()
    
    def login_by_token(self, token:str):
        """ You can get this in the settings interface of `lychee`. This interface always returns `True`
        :param token: [required] token
        """
        self._sess._header["Authorization"] = token
        return True

    def get_all_user(self):
        """ Get all users
        :return: `dict`, see `./api_demo/get_all_user.json`
        """
        return self._sess.get("UserManagement").json()
    
    def get_album(self, album:str):
        """ Get album properties and content (including detailed album information and picture information)
            :param album: [required] album_id/album_path
            :return: `dict`, see `./api_demo/get_album.json`
        """
        album_id = self.album_path2id_assert(album)
        json_info = {
            "album_id": album_id
        }
        return self._sess.get("Album", json=json_info).json()
    
    def get_albums(self):
        """ Get all albums, smart albums and unclassified pictures in the root directory
            :return: `dict`, see `./api_demo/get_albums.json`
        """
        return self._sess.get("Albums").json()

    def create_album(self, album_name:str, parent_album="/"):
        """ create an album, and return `album_id`
            :param album_name: [required] album name
            :param parent_album: parent album, default is root album
            :return: `str`, album_id
        """
        album_id = self.album_path2id_assert(parent_album)
        return self._sess.post("Album", json={
            "parent_id": album_id,
            "title": album_name
        }).text

    def delete_albums(self, albums:list):
        """ delete albums
            :param albums: [required] `album` list
            :return: `int`, is http status code
        """
        id_list = []
        for album in albums:
            if album in ["/", None]:
                continue
            id_list.append(self.album_path2id_assert(album))

        return self._sess.delete("Album", json={
            "album_ids": id_list
        }).status_code

    def search(self, terms:str, album="/"):
        """ Search keywords, you can specify the album
            :param terms: [required] Keywords
            :param album_id: album_id, default is root album
            :return: `dict`
        """
        album_id = self.album_path2id_assert(album)
        terms = base64.b64encode(terms.encode(encoding="utf-8"))
        return self._sess.get("Search", json={
            "terms": terms.decode(),
            "album_id": album_id
        }).json()

    def upload_photo(self, album, upload_filename):
        """ upload to specify the album
            :param album: default is root album
            :param upload_filename: [required] file path
            :return: `dict`, eg. {'file_name': '4.jpg', 'extension': '.jpg', 'uuid_name': 'gAA7GDjP-ru1FRsm.jpg', 'stage': 'uploading', 'chunk_number': 1, 'total_chunks': 7}
        """
        album_id = self.album_path2id_assert(album)
        chunk_size = 1024 * 1024 * 2    # 2M

        file_name = os.path.basename(upload_filename)
        file_size = os.path.getsize(upload_filename)
        chunk_count = math.ceil(file_size / chunk_size)

        uuid_name = ''
        extension = ''
        for i in range(chunk_count):
            with open(upload_filename, "rb") as f:
                r = self._sess.post("Photo", 
                            delete_headers=[
                                "Content-Type"  # requests won't add a boundary if this header is set when you pass files
                            ],
                            files={
                                'album_id': (None, album_id),
                                'file': f,
                                'file_name': (None, file_name),
                                'uuid_name': (None, uuid_name),
                                'extension': (None, extension),
                                'chunk_number': (None, f'{i+1}'),
                                'total_chunks': (None, f'{chunk_count}'),
                            })
            uuid_name = r.json()['uuid_name']
            extension = r.json()['extension']
            # print (r.json())
        return r.json()
    
    def move_album(self, target_album:str, albums=[]):
        """ move albums
            :param target_album: target album, if is void, will copy to root album
            :param albums: [required] album_ids that need to be moved, is list
            :return: `str`
        """
        target_album_id = self.album_path2id_assert(target_album)
        album_ids = []
        for album in albums:
            album_ids.append(self.album_path2id_assert(album))
        r = self._sess.post("Album::move",
                        json={
                            "album_id": target_album_id,
                            "album_ids": album_ids
                        })
        return r.json() if len(r.text) else {}

    def move_photo(self, target_album:str, photo_ids=[]):
        """ move photos
            :param target_album: target album, if is void, will copy to root album
            :param photos: [required] photo_ids that need to be moved, is list
            :return: `str`
        """
        target_album_id = self.album_path2id_assert(target_album)
        r = self._sess.post("Photo::move",
            json={
                "album_id": target_album_id,
                "photo_ids": photo_ids
            })
        return r.json() if len(r.text) else {}

    def copy_photo(self, target_album:str, photo_ids=[]):
        """ move photos
            :param target_album: target album, if is void, will copy to root album
            :param photos: [required] photo_ids that need to be moved, is list
            :return: `str`
        """
        target_album_id = self.album_path2id_assert(target_album)
        r = self._sess.post("Photo::copy",
            json={
                "album_id": target_album_id,
                "photo_ids": photo_ids
            })
        return r.json() if len(r.text) else {}
    
    def star_photo(self, is_star:bool, photo_ids=[]):
        """ Set the is-starred attribute of the given photos
            :param is_star: [required] star or not
            :param photos: [required] photo_ids that need to be star, is list
            :return: `str`
        """
        r = self._sess.post("Photo::star",
            json={
                "is_starred": is_star,
                "photo_ids": photo_ids
            })
        return r.json() if len(r.text) else {}
    
    def rename_photo(self, photo_id:str, title:str):
        """ Rename a photo
            :param photo_id: [required] photo_id
            :param title: [required] new name
            :return: `str`
        """
        r = self._sess.patch("Photo::rename",
            json={
                "photo_id": photo_id,
                "title": title
            })
        return r.json() if len(r.text) else {}
    
    def delete_photo(self, photo_ids=[]):
        """ Delete photos
            :param photos: [required] photo_ids that need to be deleted, is list
            :return: `str`
        """
        r = self._sess.delete("Photo",
            json={
                "photo_ids": photo_ids
            })
        return r.json() if len(r.text) else {}

    def get_full_tree(self):
        """ Get the complete album tree structure
            :return: `dict`, see `./api_demo/get_full_tree.json`
        """
        r = self._sess.get("Maintenance::fullTree")
        return r.json()

    def download_photo(self, url:str, save_full_name:str):
        """ download an photo to specify path
            :param url: [required] photo url
            :param save_full_name: [required] photo name
        """
        try:
            r = requests.get(url, stream=True)
            count = 0
            with open(save_full_name, "wb") as f:
                for item in r.iter_content(10240):
                    count += len(item)
                    f.write(item)
            return {"url":f"{url}", "file_name":f"{save_full_name}"}
        except Exception as e:
            raise f"Error downloading {url}: {e}"

    def download_album(self, album:str, save_path="./"):
        """ Recursively download an album
            :param album: [required] album_id/album_path
            :param save_path: [required] target path
        """
        # print (f"{album_id}:{save_path}")
        album_id = self.album_path2id_assert(album)
        os.makedirs(save_path, exist_ok=True)
        
        album_info = self.get_album(album_id)
        if "albums" in album_info["resource"].keys():
            downloaded_title = []
            for album in album_info["resource"]["albums"]:
                album_id = album["id"]
                album_title = album["title"]
                if album_title in downloaded_title:
                    album_title += f".[{album["id"]}]"
                else:
                    downloaded_title.append(album_title)
                self.download_album(album_id, os.path.join(save_path, album_title))
        
        for photo in album_info["resource"]["photos"]:
            photo_id = photo["id"]
            file_name = photo["title"]
            photo_url = photo["size_variants"]["original"]["url"]
            # file_size = photo["size_variants"]["original"]["filesize"]

            """
                The problem of Lychee allowing the same name can be solved by appending the id. If it is solved in download_photo, there will be thread insecurity issues.
                157_modify.webp -> 157_modify.[vrnzJDV5TXFCxlJ4UABQzu6G].webp
            """
            full_name = os.path.join(save_path, file_name)
            if full_name in self._file_name_list:
                tmp = file_name.split(".")
                tmp.insert(-1, f"[{photo_id}]")
                file_name = ".".join(tmp)
            else:
                self._file_name_list.append(full_name)
            self._futures.append(self._tasks_pool.submit(self.download_photo, photo_url, full_name))

    def upload_album(self, album:str, path:str, skip_exist=False):
        """ Used to upload folders to the specified directory
            :param album: album
            :param path: [required] directory to upload
            :param skip_exist: skip exist photo, default is False
        """
        album_id = self.album_path2id_assert(album)
        res = self.get_album(album_id)
        cur_title = res["resource"]["title"]
        if not res["config"]["is_accessible"]:
            raise RuntimeError(f"{album_id} Not accessible")
        title_id_map = {}
        for album in res["resource"]["albums"]:
            if album["title"] in title_id_map.keys():
                continue
            title_id_map[album["title"]] = album["id"]
        
        photo_title_list = []
        if skip_exist:
            for photo in res["resource"]["photos"]:
                photo_title_list.append(photo["title"])
            # print (photo_title_list)
        
        for entry_name in os.listdir(path):
            tmp_name = os.path.join(path, entry_name)
            if os.path.isdir(tmp_name):
                id = title_id_map.get(entry_name)
                if not id:
                    id = self.create_album(entry_name, album_id)
                self.upload_album(id, tmp_name)
            elif os.path.isfile(tmp_name):
                # 这里不判断文件是否能够上传 交由api判断 Test: 上传非图片文件、上传视频
                if skip_exist and (os.path.basename(entry_name) in photo_title_list):
                    # print (f"{entry_name} is exist")
                    continue
                self._futures.append(self._tasks_pool.submit(self.upload_photo, album_id, tmp_name))
    
    def album_path2id(self, album_path: str):
        """ Get `album_id` based on `album_path` may return multiple matching results. if you are not root user, will use get_album to get album_id, which requires multiple requests.
            :param album_path: [required] If the album path does not start with `/`, it returns `[album_path]` itself. If it starts with `/`, it returns `[None]`
            :return: Returns a `list` containing all matching `album_id`
        """
        if album_path in ["/", None, ""]:
            return [None]

        if album_path[0] != "/":
            return [album_path]
        
        path_titles = album_path.strip('/').split('/')
        res_list = []

        tree_data = self.get_full_tree()
        if isinstance(tree_data, dict): # may be {'message': 'Insufficient privileges', 'exception': 'UnauthorizedException'}
            if tree_data['message']=="Insufficient privileges":
                # print (f"无权限 尝试通过get_album获取album_id")
                def find_id(album_id, path_titles_part):
                    if len(path_titles_part) == 0:
                        return [album_id]
                    albums = self.get_album(album_id)["resource"]["albums"]
                    if len(albums) == 0:
                        return []
                    for album in albums:
                        if album['title'] == path_titles_part[0]:
                            return find_id(album['id'], path_titles_part[1:])
                    return []
                        
                albums = self.get_albums()["albums"]
                for album in albums:
                    if album['title'] == path_titles[0]:
                        res_list += find_id(album['id'], path_titles[1:])
                return res_list
            else:
                raise RuntimeError(f"{str(tree_data)}")

        id_album_dict = {album['id']: album for album in tree_data}

        def find_paths(path_titles, cur_id):
            if len(path_titles) == 0:
                if cur_id:
                    res_list.append(cur_id)
                return 

            cur_name = path_titles.pop(0)
            cur_name_album_list = [album for album in id_album_dict.values() if album["title"]==cur_name]

            for cur_name_album in cur_name_album_list:
                if cur_name_album["parent_id"] == cur_id:
                    find_paths(path_titles.copy(), cur_name_album["id"])

        find_paths(path_titles.copy(), None)

        return res_list
    
    def album_path2id_assert(self, title_path:str):
        """ The difference from `album_path2id` is that this method does not accept multiple album matches
            :param title_path: [required] album_path
            :return: album_id list, **:raise RuntimeError:** If there is no unique result, an exception is thrown.
        """
        res = self.album_path2id(title_path)
        if len(res) != 1:
            raise RuntimeError(f"{title_path} There are multiple matching results or no matching results {str(res)}If multiple matches are allowed, use album_path2id")
        return res[0]

    def album_id2path(self, album_id):
        """ Get `album_path` based on `album_id`. if you are not root user, will use get_album to get album_id, which requires multiple requests.
        :param album_id: [required] album_id
        :return: album_path
        """
        if album_id[0] == '/':
            return album_id
        tree_data = self.get_full_tree()
        path = []

        if isinstance(tree_data, dict): # may be {'message': 'Insufficient privileges', 'exception': 'UnauthorizedException'}
            if tree_data['message']=="Insufficient privileges":
                # print ("无权限，通过get_album获取album_path")
                path = []
                while True:
                    album_info = self.get_album(album_id)
                    path.insert(0, album_info["resource"]["title"])
                    if album_info["resource"]["parent_id"] == None:
                        break
                    album_id = album_info["resource"]["parent_id"]
                return "/"+"/".join(path)
            else:
                raise RuntimeError(f"{str(tree_data)}")
        
        id_album_dict = {album['id']: album for album in tree_data}
        
        if album_id not in id_album_dict:
            return ""
        
        cur_id = album_id
        while True:
            album = id_album_dict.get(cur_id, None)
            path.insert(0, album["title"])
            cur_id = album['parent_id']
            if cur_id == None:
                break

        return "/"+"/".join(path)

if __name__ == "__main__":
    client = LycheeClient("http://127.0.0.1:8802/")

    # 两种登录方式 选择其中之一
    client.login_by_passwd("root","123456")
    # client.login_by_token("5ic4uQzkOpuAlJApJfIfbA==")

    import json

    with open("../api_demo/get_all_user.json", "w") as f:
        f.write(json.dumps(client.get_all_user(), ensure_ascii=False))

    # print (client.move_photo("",["xi5LK-J01rOhu8EvxpLGxHO5"]))
    # print (client.copy_photo("NIXGEcGdYzLKgxxlNS8CdReX",["xi5LK-J01rOhu8EvxpLGxHO5"]))
    # print (client.star_photo(False, ["xi5LK-J01rOhu8EvxpLGxHO5"]))
    # print (client.rename_photo("xi5LK-J01rOhu8EvxpLGxHO5", "阿乌拉"))
    # print (client.delete_photo(["JyRgElkcPuHDzGaqzQ47w3vb"]))
    # print (client.move_album("", ["Gn6aoWZiDMXatPQVMKc6wZm0"]))


"""
 下载链接
 http://127.0.0.1:8802/api/v2/Zip?photo_ids=woCJEEe3PIRBNjrfxqBZtPho&variant=ORIGINAL

 - 下载图片接口放到Session中
 - 下载图片的接口没有设置header，可能对于加密的图片不能直接访问
 - 线程池中的任务异常不会传递出来
 - 实现分块上传
 - 跳过同名图片

 + search不能搜索_的问题
 + Album接口没办法获取根路径，需要Albums接口，但文档中没有
 + 获取的文件大小期望没有单位，以便获得准确的大小信息
 + 允许同名的考量是什么，这个就没办法简单的映射到文件系统
 + 针对同一个文件 似乎没有跳过功能了
 + 当上传之后马上删除相册会出现 {'message': 'No query results for model [App\\Models\\BaseAlbumImpl] uhtwcSrC5tCdSwIvUh6PKnCp', 'exception': 'NotFoundHttpException'} {'message': 'Creating photo failed', 'exception': 'ModelDBException'}
 + 上传的文件如果有重复文件，则不采纳二次上传的文件名
 + api接口有几个版本？
 """