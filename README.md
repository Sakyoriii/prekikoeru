用面向google和ai的散装python写了个工具...

- 多进程跑字典秒碰撞出密码
  - 密码据上次命中和命中次数排序
  - 自动尝试从压缩包名和压缩包内文件秒获取RJ号作解压密码
  - RJ号信息嵌套文件夹/压缩包继承，子压缩包尝试父压缩包上的RJ号
- 多进程解压常规音声（2~3G在我的机器上）秒解压
- 无视文件后缀无脑解压，支持分卷压缩包、视频隐写的压缩包（参考资料：([[隐写者\]](https://github.com/cenglin123/SteganographierGUI)))
- 文件日文乱码自动使用正确（shift_jis)编码解压
- 套娃压缩包自动循环解压解套娃
- 嵌套压缩包解压出来的嵌套中间路径解除
- 正则规则前置过滤（解压前）、后置过滤（解压后）。过滤不期望的重复文件
- 解压后文件夹根据RJ号爬取dlsite元数据重命名（搬[大佬的dlrename项目](https://github.com/yodhcn/dlsite-doujin-renamer)）
  - 魔改地区优先级功能，当Rj号有多个语言版本，以期望语言版本的RJ号/标题 重命名
  - 根据正则规则去除部分方括号内促销文本





13G资源解压用时约 60*5/20=15s ，cpu和磁盘都吃满了，写入峰值约1.7GB/S，均值约 13/15=0.866666666667GB/S

![image-20250322043659640](https://cdn.jsdelivr.net/gh/Sakyoriii/PicGonCDN//img/202503220437727.png)

此工具有关压缩文件的操作几乎都依赖于[7zi](https://www.7-zip.org/)命令行实现，由于未实现设定7zip路径功能，请务必正确安装7zip并[配置好相关环境变量](https://www.google.com/search?q=7zip%E7%8E%AF%E5%A2%83%E5%8F%98%E9%87%8F&oq=7zip%E7%8E%AF%E5%A2%83%E5%8F%98%E9%87%8F)后使用



怎么使用：

 - 启动项目
 - 点击'密码'，在记事本中写入要用到的解压密码，一行一个回车换行，保存文件
 - 点击'设置'打开配置文件，修改你的输出路径后保存
 - 拖拽需要解压文件到项目窗口内
 - 双击拖拽添加的列，输入备注作为一次性密码或重命名依赖的RJ号
 - 点击开冲

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

# 解压黑名单，解压时遇到黑名单内的后缀跳过解压
blacklist:
  - epub
  - pptx

#----------------------------------------dlsite-doujin-renamer 配置，参考:https://github.com/yodhcn/dlsite-doujin-renamer
scaner_max_depth: 2
scraper_locale: zh_cn
scraper_connect_timeout: 10
scraper_read_timeout: 10
scraper_sleep_interval: 3
scraper_http_proxy: null
renamer_template: '[rjcode][maker_name] work_name cv_list_str'
renamer_release_date_format: '%y%m%d'
renamer_exclude_square_brackets_in_work_name_flag: true
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
renamer_title_language_order:   # 重命名时若发现当前作品有多种语言版本，将按照当前设置优先级选择一个语言版本的元数据对文件夹进行重命名，留空或不存在将使用原始版本（估计没啥人需要英语韩语吧？所以当前只支持日简繁三种版本）
  - zh_cn
  - zh_tw
  - ja_jp
renamer_rjcode_language_order:   # 重命名时若发现当前作品有多种语言版本，将按照当前设置优先级选择一个语言版本的RJ号对文件夹进行重命名，留空将使用原始版本
  - ja_jp
#  - zh_cn
#  - zh_tw



~~~
