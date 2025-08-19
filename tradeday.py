import pandas as pd
from datetime import datetime

def count_tradeday(trade_df, start_date, end_date, date_col='trade_date'):
    """
    计算两个日期之间的交易日数量（包含首尾）

    参数:
        trade_df (pd.DataFrame): 包含交易日历的 DataFrame
        start_date (str or datetime): 起始日期
        end_date (str or datetime): 结束日期
        date_col (str): 交易日列名，默认 'trade_date'

    返回:
        int: 交易日数量
    """
    # 确保日期列为 datetime 类型
    trade_df = trade_df.copy()
    trade_df[date_col] = pd.to_datetime(trade_df[date_col])

    # 转换输入为 datetime
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    # 筛选范围内的交易日
    mask = (trade_df[date_col] >= start_date) & (trade_df[date_col] <= end_date)
    return trade_df.loc[mask].shape[0]


if __name__ =='__main__':
    # 假设你已有 trade_df
    # trade_df 示例结构：
    #     trade_date
    # 0   2020-01-01
    # 1   2020-01-02
    # ...

    # 计算 2020-04-01 到 2020-04-7 之间的交易日数量
    # path改成需要的路径
    path=r'D:\apps\中金项目\4\4\2(1).xlsx'
    trade_df=pd.read_excel(path)
    count = count_tradeday(trade_df, '2020-04-01', '2020-04-7','日期')
    print("交易日天数：", count)