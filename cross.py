import pandas as pd

def find_cross_under(df, index1, index2):
    """
    判断 index1 是否下穿 index2，返回发生下穿的 df 索引列表，并添加标记列

    参数:
    df      : pandas.DataFrame，包含 index1 和 index2 两列
    index1  : str，要检测的第一个列名
    index2  : str，要检测的第二个列名

    返回:
    df      : pandas.DataFrame，添加了 'cross_under' 列（bool 值）
    cross_indices : list，发生下穿的索引列表
    """
    # 计算前一行的差值
    prev_diff = df[index1].shift(1) - df[index2].shift(1)
    curr_diff = df[index1] - df[index2]


    # 判断是否从正变为负（即下穿）
    cross_under = (prev_diff > 0) & (curr_diff < 0)

    # 添加一列 '下穿指标'，下穿为 1，否则为 0
    df['振幅卖出指标'] = cross_under.astype(int)

    # 返回发生下穿的索引列表
    cross_indices = df.index[cross_under].tolist()

    return df

def add_weekday_column(df):
    # 确保 '日期' 列是 datetime 类型
    df['日期'] = pd.to_datetime(df['日期'])
    # 新增一列 '星期'，显示中文星期几
    weekday_map = {0: '星期一', 1: '星期二', 2: '星期三', 3: '星期四', 4: '星期五', 5: '星期六', 6: '星期日'}
    df['星期'] = df['日期'].dt.dayofweek.map(weekday_map)
    return df