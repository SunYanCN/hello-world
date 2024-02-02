#!/usr/bin/python3
# coding: utf-8

"""
已知：有4个文件，格式一样 数据是31列 100行。

第一步：把第1-10列中随机2列求和变为1列(最后得到5列)；把第11-20列中随机2列求和变为1列(最后得到5列)；把第21-30列中随机2列求和变为1列(最后得到5列)；最后得到15列；

第二步：把第1-10列中随机5列求和变为1列(最后得到2列)；把第11-20列中随机5列求和变为1列(最后得到2列)；把第21-30列中随机5列求和变为1列(最后得到2列)；最后得到6列；

第三步：求第1-10列总分；求第11-20列总分；求第21-30列总分；最后得到3列；

第四步：另存文件，即可得到4个含有24（15+6+3）列数据的文件。

要求：每一列只能被求和一次，随机且不重复。

"""
import pandas as pd
import random
from itertools import combinations

file_names = ['/home/gswewf/Downloads/test/lpa30-n100-0.5rep1.dat',
 '/home/gswewf/Downloads/test/lpa30-n100-0.5rep2.dat',
 '/home/gswewf/Downloads/test/lpa30-n100-0.5rep3.dat',
 '/home/gswewf/Downloads/test/lpa30-n100-0.5rep4.dat']

def group(ls, n):
    """
    从数组ls中随机n个值，直到数组为空
    :param ls: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    :param n: 2
    :return: [[4, 2], [3, 6], [5, 1], [7, 8], [9, 0]]
    """
    rets = []
    while(set(ls)-set(sum(rets, []))):
        new_group = random.sample(set(ls)-set(sum(rets, [])), n)
        rets.append(new_group)
    return rets
# import pandas as pd
# df =pd.DataFrame(data=[[1,2,3,2],[5,6,7,4], [9,1,2,4]])
# df
# Out[33]:
#    0  1  2  3
# 0  1  2  3  2
# 1  5  6  7  4
# 2  9  1  2  4
t10 = group([t for t in range(10)], 2)
t20 = group([t for t in range(10, 20)], 2)
t30 = group([t for t in range(20, 30)], 2)
ins = [t10, t20, t30]
ds1 = {}
for t, ts in enumerate(ins):
    for t2, tts in enumerate(ts):
        for k in tts:
            ds1[k] = t*10 + t2

def step1(x):
    '''
    第一步：把第1-10列中随机2列求和变为1列(最后得到5列)；把第11-20列中随机2列求和变为1列(最后得到5列)；把第21-30列中随机2列求和变为1列(最后得到5列)；最后得到15列；
    :param data:
    :re10turn:
    '''
    return ds1.get(x)


t10 = group([t for t in range(10)], 5)
t20 = group([t for t in range(10, 20)], 5)
t30 = group([t for t in range(20, 30)], 5)
ins = [t10, t20, t30]
ds2 = {}
for t, ts in enumerate(ins):
    for t2, tts in enumerate(ts):
        for k in tts:
            ds2[k] = t * 10 + t2


def step2(x):
    '''
    第二步：把第1-10列中随机5列求和变为1列(最后得到2列)；把第11-20列中随机5列求和变为1列(最后得到2列)；把第21-30列中随机5列求和变为1列(最后得到2列)；最后得到6列；
    :param data:
    :re10turn:
    '''
    return ds2.get(x)

def step3(x):
    '''
    第三步：求第1-10列总分；求第11-20列总分；求第21-30列总分；最后得到3列；
    :param data:
    :re10turn:
    '''
    return int(x/10)

def step4(df, path_or_buf):
    '''
    第四步：另存文件，即可得到4个含有24（15+6+3）列数据的文件。
    DataFrame.to_csv(path_or_buf=None, sep=', ', na_rep='', float_format=None, columns=None, header=True, index=True, index_label=None, mode='w', encoding=None, compression=None, quoting=None, quotechar='"', line_terminator='\n', chunksize=None, tupleize_cols=False, date_format=None, doublequote=True, escapechar=None, decimal='.', **kwds)
Write DataFrame to a comma-separated values (csv) file
    :param data:
    :re10turn:
    '''
    df.to_csv(path_or_buf, sep='\t', header=False, index=False)

for file_name in file_names:
    with open(file_name)as f:
        data = f.readlines()
        new_data = [t.strip().split()[:30] for t in data]
    new_file_name = file_name.replace('dat', 'csv')
    with open(new_file_name, 'w', encoding='utf8')as f:
        for line in new_data:
            print(','.join(line), file=f)

# for file_name in file_names:
#     df = pd.read_table(file_name, sep='     ', names=[t for t in range(30)])
    df = pd.read_table(new_file_name, sep=',', names=[t for t in range(30)])
    print(df.shape)
    grouped = df.groupby(step1, axis=1)
    t1 = grouped.agg('sum')


    grouped = df.groupby(step2, axis=1)
    t2 = grouped.agg('sum')


    grouped = df.groupby(step3, axis=1)
    t3 = grouped.agg('sum')

    t4 = pd.concat([t1, t2, t3], axis=1)

    path_or_buf = file_name.replace('lpa30-n100-0.5', 'result_')
    step4(t4, path_or_buf)

    # data = pd.read_table('Z:/test.txt', header=None, encoding='gb2312', delim_whitespace=True, index_col=0)
    # header=None:没有每列的column name，可以自己设定
    # encoding='gb2312':其他编码中文显示错误
    # delim_whitespace=True:用空格来分隔每行的数据
    # index_col=0:设置第1列数据作为index
    # data.iloc[1], 第2行
    # data.icol(0) #， 第一列
    # data.iloc[:, 0] #， 第一列

    # 利用Pandas库中的sample。
    # DataFrame.sample(n=None, frac=None, replace=False, weights=None, random_state=None, axis=None)
    # n是要抽取的行数。（例如n = 20000
    # 时，抽取其中的2W行）
    # frac是抽取的比列。（有一些时候，我们并对具体抽取的行数不关系，我们想抽取其中的百分比，这个时候就可以选择使用frac，例如frac = 0.8，就是抽取其中80 %）
    # replace抽样后的数据是否代替原DataFrame()
    # weights这个是每个样本的权重，具体可以看官方文档说明。
    # random_state这个在之前的文章已经介绍过了。
    # axis是选择抽取数据的行还是列。axis = 0的时是抽取行，axis = 1时是抽取列（也就是说axis = 1时，在列中随机抽取n列，在axis = 0时，在行中随机抽取n行）
    # apply()对dataframe的内容进行批量处理, 这样要比循环来得快。如df.apply(func,axis=0,.....) func：定义的函数，axis=0时为对列操作，=1时为对行操作。


def main():
    pass


if __name__ == '__main__':
    main()

# #对列的操作方法有如下几种
#
# data.icol(0)   #选取第一列
# data.ix[:,[0,1,2]]  #不知道列名只知道列的位置时
# data.ix[1,[0]]  #选择第2行第1列的值
# data.ix[[1,2],[0]]   #选择第2,3行第1列的值
# data.ix[1:3,[0,2]]  #选择第2-4行第1、3列的值
# data.ix[1:2,2:4]  #选择第2-3行，3-5（不包括5）列的值
# data.ix[data.b>6,3:4]  #选择'b'列中大于6所在的行中的第4列，有点拗口
# data.ix[data.a>5,2:4]  #选择'a'列中大于5所在的行中的第3-5（不包括5）列
# data.ix[data.a>5,[2,2,2]]  #选择'a'列中大于5所在的行中的第2列并重复3次
# data.irow(1)   #选取第二行
# data.ix[1]   #选择第2行
# data['one':'two']  #当用已知的行索引时为前闭后闭区间，这点与切片稍有不同。
# data.ix[1:3]  #选择第2到4行，不包括第4行，即前闭后开区间。
# data.ix[-1:]  #取DataFrame中最后一行，返回的是DataFrame类型,**注意**这种取法是有使用条件的，只有当行索引不是数字索引时才可以使用，否则可以选用`data[-1:]`--返回DataFrame类型或`data.irow(-1)`--返回Series类型
# data[-1:]  #跟上面一样，取DataFrame中最后一行，返回的是DataFrame类型
# data.ix[-1] #取DataFrame中最后一行，返回的是Series类型，这个一样，行索引不能是数字时才可以使用
# data.tail(1)   #返回DataFrame中的最后一行
# data.head(1)   #返回DataFrame中的第一行



