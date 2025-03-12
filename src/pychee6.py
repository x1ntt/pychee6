from requests import Session
from urllib.parse import unquote
from concurrent.futures import ThreadPoolExecutor, wait
import requests
import base64
import os
import time
import shutil
import sys

class LycheeSession(Session):
    def __init__(self, base_url):
        super().__init__()
        # api地址，目前仅支持v2
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
    """ 约定

    + `album_id`: 相册id必须是24字节长度的字符串
    + `album_path`: 相册路径 必须是`/`开头 如果仅有`/`则表示根相册
    """
    def __init__(self, base_url:str, max_workers:int=5):
        """ 
            :param base_url: lychee的api地址 如 `http://127.0.0.1:5000/`
            :param max_workers: 下载最大线程数
        """
        self._sess = LycheeSession(base_url)

        self._tasks_pool = ThreadPoolExecutor(max_workers=max_workers)
        self._futures = []
        self._file_name_list = []
    
    def wait_tasks(self):
        wait(self._futures)
        self._futures = []

    def login_by_passwd(self, username:str, password:str):
        """ 通过账号密码登录
        :param username: 用户名
        :param password: 密码

        :return: 返回一个`tuple`, (res:bool, reason:dict)
        """
        r = self._sess.post("Auth::login", json={
            "username": username, 
            "password": password
        })
        if r.status_code == 204:
            return True, r.json()
        return False, r.json()
    
    def login_by_token(self, token:str):
        """ 你可以在`lychee`的设置界面获得 这个接口始终返回`True`
        :param token: token
        """
        self._sess._header["Authorization"] = token
        return True
    
    def get_album(self, album:str):
        """ 获取相册属性和内容（包含详细的相册信息和图片信息）
            :param album: album_id/album_path
            :return: 返回一个`dict`, 结构形如 `./api_demo/get_album.json`
        """
        album_id = self.album_path2id_assert(album)
        json_info = {
            "album_id": album_id
        }
        return self._sess.get("Album", json=json_info).json()
    
    def get_albums(self):
        """ 获取根目录下的所有相册以及智能相册以及未分类图片
            :return: 返回一个`dict`, 结构形如 `./api_demo/get_albums.json`
        """
        return self._sess.get("Albums").json()

    def create_album(self, album_name:str, parent_album="/"):
        """ 创建一个相册并返回相册id
            :param album_name: 相册名字
            :param parent_album: 父相册 默认为根相册
            :return: 返回一个`str`, album_id
        """
        album_id = self.album_path2id_assert(parent_album)
        return self._sess.post("Album", json={
            "parent_id": album_id,
            "title": album_name
        }).text

    def delete_albums(self, albums:list):
        """ 删除一些相册 
            :param albums: `album` 列表
            :return: 返回一个`int`, 作为状态码
        """
        id_list = []
        for album in albums:
            id_list.append(self.album_path2id_assert(album))

        return self._sess.delete("Album", json={
            "album_ids": id_list
        }).status_code

    def search(self, terms:str, album=""):
        """ 搜索关键字，可以指定相册(似乎这个接口有问题)
            :param terms: 搜索关键字
            :param album_id: album_id 默认为根相册
            :return: 返回一个`dict`
        """
        album_id = self.album_path2id_assert(album)
        terms = base64.b64encode(terms.encode(encoding="utf-8"))
        return self._sess.get("Search", json={
            "terms": terms.decode(),
            "album_id": album_id
        }).json()

    def upload_photo(self, album, upload_filename):
        """ 上传照片到指定相册id(这个接口似乎不能跳过已经上传的文件)
            :param upload_filename: 上传文件名
            :param album_id: album_id 默认为根相册
            :return: 返回一个`dict`
        """
        album_id = self.album_path2id_assert(album)

        with open(upload_filename, "rb") as f:
            r = self._sess.post("Photo", 
                        delete_headers=[
                            "Content-Type"  # requests won't add a boundary if this header is set when you pass files
                        ],
                        files={
                            'album_id': (None, album_id),
                            # 'file_last_modified_time': (None, '123456'),
                            'file': f,
                            'file_name': (None, os.path.basename(upload_filename)),
                            'uuid_name': (None, ''),
                            'extension': (None, ''),
                            'chunk_number': (None, '1'),
                            'total_chunks': (None, '1'),
                        })
            return r.json()
    
    def move_album(self, target_album:str, albums=[]):
        """ 移动相册
            :param target_album: 目标相册
            :param albums: 需要移动的相册id列表
            :return: 返回一个`str`
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
        return r.text
    
    def get_full_tree(self):
        """ 获取完整的相册树形结构
            :return: 返回一个`dict`, 形如 `./api_demo/get_full_tree.json`
        """
        r = self._sess.get("Maintenance::fullTree")
        return r.json()

    def download_photo(self, url:str, file_name:str, dist_path:str):
        """ 下载一张图片到指定路径
            :param url: 图片url
            :param file_name: 图片文件名
            :param dist_path: 保存路径
        """
        try:
            r = requests.get(url, stream=True)
            count = 0
            with open(os.path.join(dist_path, file_name), "wb") as f:
                for item in r.iter_content(10240):
                    count += len(item)
                    f.write(item)
        except Exception as e:
            raise f"Error downloading {url}: {e}"

    def download_album(self, album:str, save_path="./"):
        """ 递归下载某个相册 将会添加任务到downloader
            :param album: album
            :param save_path: 保存路径
        """
        # print (f"{album_id}:{save_path}")
        album_id = self.album_path2id_assert(album)
        os.makedirs(save_path, exist_ok=True)
        # 获取路径下所有的相册 将图片加入下载器 相册继续遍历
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
                针对lychee允许同名的问题 通过追加id的方式解决 如果在download_photo中解决会有线程不安全的问题
                157_modify.webp -> 157_modify.[vrnzJDV5TXFCxlJ4UABQzu6G].webp
            """
            full_name = os.path.join(save_path, file_name)
            if full_name in self._file_name_list:
                tmp = file_name.split(".")
                tmp.insert(-1, f"[{photo_id}]")
                file_name = ".".join(tmp)
            else:
                self._file_name_list.append(full_name)
            self._futures.append(self._tasks_pool.submit(self.download_photo, photo_url, file_name, save_path))

    def upload_album(self, album:str, path:str):
        """ 用于上传文件夹到指定目录
            :param album: album
            :param path: 待上传的目录
        """
        album_id = self.album_path2id_assert(album)
        res = self.get_album(album_id)
        cur_title = res["resource"]["title"]
        if not res["config"]["is_accessible"]:
            raise RuntimeError(f"{album_id} 不可访问")
        title_id_map = {}
        for album in res["resource"]["albums"]:
            if album["title"] in title_id_map.keys():
                # print(f"Waring {cur_title}中有多个名为{album["title"]}的相册 图片将会上传到第一个同名相册")
                continue
            title_id_map[album["title"]] = album["id"]
        
        for entry_name in os.listdir(path):
            tmp_name = os.path.join(path, entry_name)
            if os.path.isdir(tmp_name):
                id = title_id_map.get(entry_name)
                if not id:
                    id = self.create_album(entry_name, album_id)
                self.upload_album(id, tmp_name)
            elif os.path.isfile(tmp_name):
                # 这里不判断文件是否能够上传 交由api判断 Test: 上传非图片文件、上传视频
                self._futures.append(self._tasks_pool.submit(self.upload_photo, album_id, tmp_name))
    
    def album_path2id(self, album_path: str):
        """ 根据`album_path`获取`album_id` 可能返回多个匹配结果
            :param album_path: 相册路径 如果不是`/`开头则返回`[album_path]`本身 如果是`/`则返回`[None]`
            :return: 返回一个`list`, 内容为所有匹配的`album_id`
        """
        if album_path in ["/", None, ""]:
            return [None]

        if album_path[0] != "/":
            return [album_path]
        
        tree_data = self.get_full_tree()
        path_titles = album_path.strip('/').split('/')
        
        id_album_dict = {album['id']: album for album in tree_data}

        res_list = []

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
        """ 和`album_path2id`的区别在于，这个方法不接受多个相册匹配
            :param title_path: 相册路径
            :return: 相册id列表
            :raise: 如果有多个相册或者没有匹配则抛出异常
        """
        res = self.album_path2id(title_path)
        if len(res) != 1:
            raise RuntimeError(f"{title_path} 有多个匹配结果或者没有匹配结果 {str(res)} 如果允许多个匹配请使用album_path2id")
        return res[0]

    def album_id2path(self, album_id):
        """ 根据`album_id`获取`album_path`
        :param album_id: album_id
        :return: 相册路径
        """
        if album_id[0] == '/':
            return album_id
        tree_data = self.get_full_tree()
        id_album_dict = {album['id']: album for album in tree_data}
        
        if album_id not in id_album_dict:
            return ""

        path = []
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

    # with open("api_demo/get_full_tree.json", "w") as f:
    #     f.write(json.dumps(client.get_full_tree(), ensure_ascii=False))

    print (client.album_path2id("/一层/二层"))
    print (client.album_id2path("b4noPnuHQSSCXZL_IMsLEGAJ"))

    sys.exit()

    testtest_id = client.create_album("testtest")
    print (f"创建测试相册: {testtest_id}")

    # 上传一个文件夹中的内容到新建相册
    client.upload_album(testtest_id, "./img")

    wait(client._futures)

    res = client.get_album(testtest_id)
    for photo_name in ["157_modify.webp", "jwe8iur92.jpg", "wallhaven-yx7vjk.png"]:
        if photo_name not in [x["title"] for x in res["resource"]["photos"]]:
            print (f"Error: 文件上传可能失败 {photo_name} 没有成功上传 {[x["title"] for x in res["resource"]["photos"]]}")
    print (client._sess._header)

    for album_name in ["deepth2"]:
        if album_name not in [x["title"] for x in res["resource"]["albums"]]:
            print (f"Error: 创建相册可能失败 {album_name} 没有成功上传 {[x["title"] for x in res["resource"]["albums"]]}")
    
    time.sleep(0.5)

    testtest_id2 = client.create_album("testtest2")
    print (f"创建测试相册: {testtest_id2}")

    client.move_album(testtest_id2, [testtest_id])

    time.sleep(0.5)

    res = client.get_album(testtest_id2)

    for album_name in ["testtest"]:
        if album_name not in [x["title"] for x in res["resource"]["albums"]]:
            print (f"Error2: 移动相册可能失败 {album_name} 没有成功上传 {[x["title"] for x in res["resource"]["albums"]]}")

    time.sleep(0.5)

    client.download_album(testtest_id2, "./img")
    time.sleep(0.5)
    client.delete_albums([testtest_id, testtest_id2])
    shutil.rmtree("./img/testtest", True)

    # res = client.search("testtest")
    # for album in res['albums']:
    #     if album['title'] == "testtest":
    #         client.delete_albums([album['id']])
    #         print (f"删除: {album['id']}")

    # print ("----------")
    # print (json.dumps(client.get_album("QVTko4XqcIK3VPzuCXAB_I3T"), ensure_ascii=False))
    # print (json.dumps(client.get_albums(), ensure_ascii=False))

    # for album in client.get_albums()["albums"]:
    #     client.download_album(album["id"], "./img")
    # client.download_album("unsorted", "./img")
    # client._tasks_pool.shutdown()

    # print (client.upload_photo("./157_modify.webp", "QVTko4XqcIK3VPzuCXAB_I3T"))
    # print (client.move_album("-WnvWIQ_K9R2wqvnFBigvVJC", ["QVTko4XqcIK3VPzuCXAB_I3T", "zUTB2k8memPLyYdfpyK0BCof"]))

    # print (json.dumps(client.get_full_tree(), ensure_ascii=False))

    # client._tasks_pool.shutdown()


"""
 下载链接
 http://127.0.0.1:8802/api/v2/Zip?photo_ids=woCJEEe3PIRBNjrfxqBZtPho&variant=ORIGINAL

 - 下载图片接口放到Session中
 - 下载图片的接口没有设置header，可能对于加密的图片不能直接访问
 - 线程池中的任务异常不会传递出来
 - 实现分块上传

 + search不能搜索_的问题
 + Album接口没办法获取根路径，需要Albums接口，但文档中没有
 + 获取的文件大小期望没有单位，以便获得准确的大小信息
 + 允许同名的考量是什么，这个就没办法简单的映射到文件系统
 + 针对同一个文件 似乎没有跳过功能了
 + 当上传之后马上删除相册会出现 {'message': 'No query results for model [App\\Models\\BaseAlbumImpl] uhtwcSrC5tCdSwIvUh6PKnCp', 'exception': 'NotFoundHttpException'} {'message': 'Creating photo failed', 'exception': 'ModelDBException'}
 + 上传的文件如果有重复文件，则不采纳二次上传的文件名
 + api接口有几个版本？
 """