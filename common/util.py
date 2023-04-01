import zipfile


def cbk(a, b, c):
    """
    func:
        回调函数
    params:
        a:已经下载的数据块
        b:数据块的大小
        c:远程文件的大小
    """
    per = 100.0*a*b/c
    if per > 100:
        per = 100
    print('\r'+'[下载进度]:%s%.2f%%' % ('>'*int(a*b*50/c), float(per)), end=' ')
    if per == 100:  # 解决end=''引发的不换行
        print()


def unzip(zip_file, store_dir="./"):
    f = zipfile.ZipFile(zip_file, 'r')
    for file in f.namelist():
        f.extract(file, store_dir)
    f.close()