��    %      D  5   l      @  6   A  l   x     �  '   �  (      n   I  l   �     %  7   D     |  1   �     �     �  w   �     m     �     �     �  .   �  B   �     .     G  7   \  `   �  �  �  >   �	     �	  7   �	  >   &
     e
  B   v
     �
  :   �
          2     @    P  6   h  `   �        ,     *   E  z   p  w   �     c  2   �     �  ,   �     �       q   !     �     �     �     �  /   �  6        B     X  6   n  Z   �  �     5   �  9   �  2   #  ;   V     �  9   �  !   �  B   �      B     c     s            #          	         
                       %                                                               "              !                            $                    '{path}' is not a valid directory or it does not exist API token required for login, alternative to username. Can be provided via LYCHEE_TOKEN environment variable Album id to delete Album id, can be '/' leading album path Based on title name skip existing photos Can be album id or '/' leading album path, if it starts with '-', then need to add '--', like list -- -iw78289 Can be album id or '/' leading album path, if it starts with '-', then need to add '--list_album -- -iw78289 Cannot find album for ID: {id} Create album, album_id as '/' then create album in root Delete specified album Download album, album_id as '/' then download all Download target directory List album and photos Need provide login information, can specify user and passwd parameters, or provide via environment variables (see help) New album id: {id} New album name Only display albums Output debug information Parent album id, can be '/' leading album path Password. Can be provided via LYCHEE_PASSWORD environment variable Path to upload directory Path to upload photo Register upload/download function to mouse context menu Server address, like: http://exp.com:8808/. Can be provided via LYCHEE_HOST environment variable This is the CLI version of LycheeClient, which can be used as an example of library usage.
In most cases, you can use album_id or album path as parameters.
	album_id is a 24-character string like: b4noPnuHQSSCXZL_IMsLEGAJ
	Album path starts with / like: /depth_1/depth_2. Single / represents root directory or unsorted
	For issues or suggestions, please create an issue at: https://github.com/x1ntt/pychee6 😉 Thread pool size affecting upload/download count, default is 5 Unregister mouse context menu Upload album, album_id as '/' then upload to root album Upload photo to album, album_id as '/' then upload to unsorted Upload to Lychee Username. Can be provided via LYCHEE_USERNAME environment variable album_id and album_path switch album_id and album_path switch, album path starts with '/' ✨Refresh (if album modified) ❌Unregister 🔻Upload here Project-Id-Version: PACKAGE VERSION
Report-Msgid-Bugs-To: 
PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE
Last-Translator: FULL NAME <EMAIL@ADDRESS>
Language-Team: LANGUAGE <LL@li.org>
Language: 
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
 '{path}' 不是一个合法的目录或者它不存在 登录所需要的api token，与用户名二选一 可以通过 LYCHEE_TOKEN 环境变量提供 需要删除的相册id 相册id，可以为'/'开头的相册路径 根据标题名跳过已经存在的图片 可以是相册id或者'/'开头的相册路径，如果以'-'开头，则需要在前面补充--，形如list -- -iw78289 可以是相册id或者'/'开头的相册路径，如果以'-'开头，则需要在前面补充--list_album -- -iw78289 找不到 {id} 对应的相册 创建相册，album_id为'/'则在根相册创建 删除指定相册 下载相册，album_id为'/'则下载所有 下载的目标目录 列出相册和图片 需要提供登录信息，可以指定 user和passwd参数，或者通过环境变量提供（见帮助信息） 新相册id: {id} 新相册的名字 仅显示相册 输出调试信息 父相册id，可以为'/'开头的相册路径 密码 可以通过环境变量 LYCHEE_PASSWORD 提供 需要上传的目录 需要上传的图片 将上传下载功能注册到鼠标上下文菜单中 服务器地址，形如: http://exp.com:8808/ 可以通过环境变量 LYCHEE_HOST 提供 这是LycheeClient的cli版本，你可以把这个当作库的使用示例。
大多数情况下，你可以使用album_id或者相册路径为参数。
	album_id是一个24位长度的字符串形如：b4noPnuHQSSCXZL_IMsLEGAJ。
	相册路径是以/开头的字符串形如：/deepth_1/deepth_2。其中单独的/表示根目录或者说未分类
	如果有问题或者建议欢迎提出issue: https://github.com/x1ntt/pychee6 😉 线程池大小 影响上传下载数量，默认为5 取消注册鼠标上下文菜单中的上传下载功能 上传相册，album_id为'/'则上传到根相册 上传图片到相册，album_id为'/'则上传到未分类 上传到 Lychee 用户名 可以通过环境变量 LYCHEE_USERNAME 提供 album_id和album_path互相转换 album_id 和 album_path 相互转换，相册路径需以'/'开头 ✨刷新(如果相册有修改) ❌取消注册 🔻上传到此处 