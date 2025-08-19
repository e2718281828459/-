import pandas as pd
import numpy as np
from datetime import timedelta
import tradeday as td
from cross import find_cross_under
from cross import add_weekday_column

def function(df):
    # 1. 预处理数据
    df = add_weekday_column(df)  # 添加星期列
    df['日期'] = pd.to_datetime(df['日期'])
    
    # 2. 初始化输出列
    df['振幅距离预警的日期'] = 0
    df['振幅指标调整仓位'] = 0.0
    df['振幅卖出指标'] = 0  # 记录下穿
    df['振幅预警指标'] = 0
    df['振幅距离基准的日期'] = np.nan  # 使用 np.nan 初始化，允许混合类型
    df['振幅距离基准的日期'] = df['振幅距离基准的日期'].astype('object')  # 设置为 object 类型

    # 3. 初始化计数器
    first_date = df['日期'].iloc[0]  # 第一次观察日期
    last_date = None  # 预警开始日期
    obs_cnt = 0  # 观察计数
    flag = 0  # 预警触发标志
    sell_done = False  # 是否已卖出

    # 4. 计算下穿指标
    df = find_cross_under(df, '收盘价', '日度BBI')

    # 5. 逐行扫描
    for idx, row in df.iterrows():
        dt = row['日期']
        amp = row['振幅(%)']
        drop = row['涨跌幅(%)']
        weekday = row['星期'].strip()
        cross_down = row['振幅卖出指标']

        # 计算距离基准日期的交易日数
        df.at[idx, '振幅距离基准的日期'] = td.count_tradeday(df, first_date.date(), dt.date(), '日期')

        # ① 触发观察计数
        if amp > 2.5 and drop < 0 and not sell_done:
            obs_cnt += 1
            df.at[idx, '振幅预警指标'] = 1
            if obs_cnt == 1:
                first_date = dt  # 设置基准日期
                df.at[idx, '振幅距离基准的日期'] = '基准'
            if obs_cnt == 3:
                last_date = dt  # 标记预警开始日期
                flag = 1  # 触发预警

        # ② 预警后 30 天内未下穿或 60 天周期结束，清零计数
        if flag == 1 and last_date is not None:
            if td.count_tradeday(df, last_date.date(), dt.date(), '日期') > 30:
                last_date, obs_cnt, flag = None, 0, 0
        if flag == 0 and td.count_tradeday(df, first_date.date(), dt.date(), '日期') > 60:
            obs_cnt, sell_done = 0, False
            first_date = dt  # 重置基准日期

        # ③ 预警后 30 天内下穿，确定卖出日期
        if flag == 1 and not sell_done and td.count_tradeday(df, last_date.date(), dt.date(), '日期') < 30:
            if cross_down == 1:
                # 根据星期确定卖出日期
                if weekday in ['星期一', '星期二','星期五']:
                    # 当周周五
                    sell_date = dt + pd.offsets.Week(weekday=4)  # 4 表示周五
                else:  # 周三、周四
                    # 下周周五
                    sell_date = dt + pd.offsets.Week(weekday=4) + pd.offsets.Week(1)
                
                # 确保卖出日期在数据范围内
                if sell_date in df['日期'].values:
                    sell_idx = df[df['日期'] == sell_date].index[0]
                    date_str1 = dt.strftime('%Y-%m-%d')
                    date_str2 = sell_date.strftime('%Y-%m-%d')
                    print(f"{date_str1} 下穿！{date_str2} 卖出！")
                    df.at[sell_idx, '振幅指标调整仓位'] = -0.15
                    last_date, flag, obs_cnt, sell_done = None, 0, 0, True

        # ④ 更新“振幅距离预警的日期”
        if last_date is not None and flag == 1:
            df.at[idx, '振幅距离预警的日期'] = td.count_tradeday(df, last_date.date(), dt.date(), '日期')

    return df

if __name__ == '__main__':
    # 1. 读取数据
    path = r"D:\apps\中金项目\7-29-收益率\mian7月31日\main1\main\resource\resource.xlsx"
    out_file = r"D:\apps\中金项目\7-29-收益率\mian7月31日\main1\main\result\result44444444444.xlsx"
    df = pd.read_excel(path)
    df = function(df)
    df.to_excel(out_file, index=False)