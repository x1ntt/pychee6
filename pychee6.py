from requests import Session
from urllib.parse import unquote
from concurrent.futures import ThreadPoolExecutor, wait
from pathlib import Path
import requests
import base64
import os
import json
import time
import logging
import shutil
import sys

logging.basicConfig(level=logging.INFO, format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
loger = logging.getLogger("lycheeclient")
# loger.setLevel(logging.DEBUG)

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
        loger.debug(f"{method}: {url}")
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
    def __init__(self, base_url:str, max_workers:int=5):
        self._sess = LycheeSession(base_url)

        self._tasks_pool = ThreadPoolExecutor(max_workers=max_workers)
        self._futures = []
        self._file_name_list = []

    def login_by_passwd(self, username, password):
        r = self._sess.post("Auth::login", json={
            "username": username, 
            "password": password
        })
        if r.status_code == 204:
            return True, ""
        return False, r.text
    
    def login_by_token(self, token):
        self._sess._header["Authorization"] = token
        return True
    
    # 获取相册属性和内容（包含详细的相册信息和图片信息），必须指定album_id
    # ./api_demo/get_album.json
    def get_album(self, album_id:str):
        json_info = {
            "album_id": album_id
        }
        return self._sess.get("Album", json=json_info).json()
    
    # 获取根目录下的所有相册，与上一个接口返回的数据结构不同
    # ./api_demo/get_albums.json
    def get_albums(self):
        return self._sess.get("Albums").json()

    # 创建一个相册，返回相册id
    def create_album(self, album_name, parent_id="/"):
        print (f"创建相册: {album_name}, {parent_id}")
        if parent_id =="/":
            parent_id = None
        return self._sess.post("Album", json={
            "parent_id": parent_id,
            "title": album_name
        }).text

    # 删除一些相册
    def delete_albums(self, album_ids:list):
        # 成功与否都会返回204状态码，所以需要自行考虑成功或失败的问题
        return self._sess.delete("Album", json={
            "album_ids": album_ids
        }).status_code

    # 搜索关键字，可以指定相册(似乎这个接口有问题)
    def search(self, terms, album_id=""):
        terms = base64.b64encode(terms.encode(encoding="utf-8"))
        return self._sess.get("Search", json={
            "terms": terms.decode(),
            "album_id": album_id
        }).json()

    # 上传照片，可以指定相册id（这个接口似乎不能跳过已经上传的文件）
    def upload_photo(self, upload_filename, album_id="/"):
        print (f"上传照片: {upload_filename},{album_id}")
        if album_id == "/":
            album_id = None
        try:
            with open(upload_filename, "rb") as f:
                r = self._sess.post("Photo", 
                            delete_headers=[
                                "Content-Type"  # requests won't add a boundary if this header is set when you pass files
                            ],
                            files={
                                'album_id': (None, album_id),
                                'file_last_modified_time': (None, '123456'),
                                'file': f,
                                'file_name': (None, os.path.basename(upload_filename)),
                                'uuid_name': (None, ''),
                                'extension': (None, ''),
                                'chunk_number': (None, '1'),
                                'total_chunks': (None, '1'),
                            })
                print (f"上传完毕: {upload_filename} r.json() {r.json()}")
                return r.json()
        except Exception as e:
            print (f"上传失败: {str(e)}")
    
    def move_album(self, target_album, album_ids=[]):
        r = self._sess.post("Album::move",
                        json={
                            "album_id": target_album,
                            "album_ids": album_ids
                        })
        return r.text
    
    def get_full_tree(self):
        r = self._sess.get("Maintenance::fullTree")
        return r.json()

    # 实用接口
    def download_photo(self, url, file_name, dist_path):
        try:
            r = requests.get(url, stream=True)
            count = 0
            with open(os.path.join(dist_path, file_name), "wb") as f:
                for item in r.iter_content(10240):
                    count += len(item)
                    f.write(item)
        except Exception as e:
            print(f"Error downloading {url}: {e}")

    def download_album(self, album_id:str, save_path="./"):
        """
            递归下载某个相册 将会添加任务到downloader
        """
        print (f"{album_id}:{save_path}")
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
                针对lychee允许同名的问题 通过追加id的方式解决 在download_photo中解决会有线程不安全的问题
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

    def upload_album(self, album_id:str, path:str):
        """
            用于上传文件夹到指定目录
        """
        res = self.get_album(album_id=album_id)
        cur_title = res["resource"]["title"]
        if not res["config"]["is_accessible"]:
            raise RuntimeError(f"{album_id} 不可访问")
        title_id_map = {}
        for album in res["resource"]["albums"]:
            if album["title"] in title_id_map.keys():
                print(f"Waring {cur_title}中有多个名为{album["title"]}的相册 图片将会上传到第一个同名相册")
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
                self._futures.append(self._tasks_pool.submit(self.upload_photo, tmp_name, album_id))
    
    # 根据相册路径获取album_id，可能返回多个匹配结果
    def album_path2id(self, title_path: str):
        tree_data = self.get_full_tree()
        path_titles = title_path.strip('/').split('/')
        
        # 创建一个字典来快速查找节点
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

    def album_id2path(self, album_id):
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
 - 实现路径到id的转换
 - 实现自动判断路径和id (路径必须/开头)

 + search不能搜索_的问题
 + Album接口没办法获取根路径，需要Albums接口，但文档中没有
 + 获取的文件大小期望没有单位，以便获得准确的大小信息
 + 允许同名的考量是什么，这个就没办法简单的映射到文件系统
 + 针对同一个文件 似乎没有跳过功能了
 + 当上传之后马上删除相册会出现 {'message': 'No query results for model [App\\Models\\BaseAlbumImpl] uhtwcSrC5tCdSwIvUh6PKnCp', 'exception': 'NotFoundHttpException'} {'message': 'Creating photo failed', 'exception': 'ModelDBException'}
 + 上传的文件如果有重复文件，则不采纳二次上传的文件名
 + api接口有几个版本？
 """