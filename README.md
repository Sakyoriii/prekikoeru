
用面向google和ai的散装python写了个工具...

- 跑字典解压压缩包
- 日文乱码自动用shift_jis编码解压
- 尝试使用多进程解压（多进程解压同一个压缩文件中的不同文件、非多进程同时解压多个压缩文件。性能提升未知）
- 解压出来的压缩包自动继续解压（套娃压缩文件）
- 解压的套娃压缩包可能会造成文件夹套娃，所以文件夹也解套娃
- 根据正则匹配文件名方式过滤文件（解压前过滤解压文件list、解压后过滤输出文件）
- 根据JR号爬dlsite元数据重命名照搬[大佬的dlrename项目](https://github.com/yodhcn/dlsite-doujin-renamer)

此工具有关压缩文件的操作几乎都依赖于[7zi](https://www.7-zip.org/)命令行实现，由于未实现设定7zip路径功能，请务必正确安装7zip并[配置好相关环境变量](https://www.google.com/search?q=7zip%E7%8E%AF%E5%A2%83%E5%8F%98%E9%87%8F&oq=7zip%E7%8E%AF%E5%A2%83%E5%8F%98%E9%87%8F)后使用



怎么使用：
 - 启动项目
 - 点击'密码'，在记事本中写入要用到的解压密码，一行一个回车换行，保存文件
 - 点击'设置'打开配置文件，修改你的输出路径后保存
 - 拖拽需要解压文件到项目窗口内，点击'开冲'


简单sample
[![example](https://cdn.jsdelivr.net/gh/Sakyoriii/PicGonCDN//img/202408061717707.png)](https://cdn.jsdelivr.net/gh/Sakyoriii/PicGonCDN//img/202408061702433.mp4)


配置文件
~~~yaml
path:
# 解压文件输出路径
  output: "F:\\下载缓冲\\音声中继"
# 假装删除用的回收站
  recycle: "F:\\下载缓冲\\recycle"

# TIP: 为了预防解压或过滤失败后原来的压缩包被删除以及避免各种因测试用例没有覆盖所遗留的BUG，
# 强烈建议开启假删除后把所有中间生成的压缩包自动删除全设置为TRUE（即除了del_after_unzip其他del_xxx全设为true）
# 然后在确认输出文件无误后手动删除recycle和最初的压缩包

# 假装删除
logical_deletion: true
# 解压后是否自动删除
del_after_unzip: false
# 合并分卷后自动删除分卷
#del_after_merged: true
# 合并的分卷解压后自动删除（废弃）
#del_after_merged_and_unzip: true
# 解压套娃压缩后自动删除,建议开启，关闭影响文件去套娃功能（废弃）
del_after_reunzip: true
# 自动跳到下一步   exp：主要分三步, 解压(解压-去除冗余文件夹-寻找压缩包-解压......loop) -> 插入RJ到文件夹名 -> 过滤 -> 根据RJ重命名
auto_next: true
# 多线程解压(改成多进程了) 请根自己机器配置设置，参考：13600KF + Samsung 980 推荐设置 = 6
max_thread: 6

# 解压后过滤不需要的文件或文件夹，使用正则
filter:
  # 是否过滤文件夹
  filte_dir: true
  keyword:
    # 根据需求自选选择过滤关键词，行首添加 “#” 井号关闭该规则，删除井号开启规则。自定义规则清自行百度/谷歌：正则表达式
     # 过滤没有SE的WAV文件
    - (?:SE|音|音效)(?:[な無]し|CUT).*\.WAV$|(?:NO|无)(?:SE|音效).*\.WAV$
    # 过滤没有SE的文件夹
    - WAV.*(?:SE|音|音效)(?:[な無]し|CUT)[^\\]*$|(?:SE|音|音效)(?:[な無]し|CUT)[^\.]WAV[^\\]*$|WAV.*(?:NO|无)(?:SE|音效)[^\\]*$|(?:NO|无)(?:SE|音效)[^\.]*WAV[^\\]*$
    # 过滤所有没有SE的文件和文件夹
    # - (?:SE|音)(?:[な無]し|CUT)|NOSE

#    - "MP3"         # 过滤mp3
    - "FULL"        # 过滤不分トラック的长音频
    - "反転"        # 过滤左右音轨反转的文件和文件夹

#----------------------------------------dlsite-doujin-renamer 配置，参考:https://github.com/yodhcn/dlsite-doujin-renamer
scaner_max_depth: 2
scraper_locale: zh_cn
scraper_connect_timeout: 10
scraper_read_timeout: 10
scraper_sleep_interval: 3
scraper_http_proxy: null
renamer_template: '[rjcode][maker_name] work_name cv_list_str'
renamer_release_date_format: '%y%m%d'
renamer_exclude_square_brackets_in_work_name_flag: false
renamer_illegal_character_to_full_width_flag: false
make_folder_icon: true
remove_jpg_file: true
renamer_delimiter: ' '
cv_list_left: '(CV '
cv_list_right: )
renamer_tags_max_number: 5
renamer_tags_ordered_list:
  - 标签1
  - - 标签2
    - 替换2
  - 标签3



~~~


