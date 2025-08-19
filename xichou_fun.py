import pandas as pd
import os
from tradeday import count_tradeday as CD

def xichou(df):
    """
    吸筹策略函数，基于吸筹值和价格变化进行买入卖出吸筹买卖，并在每次卖出时计算收益率。
    参数:
        df (pd.DataFrame): 包含'日期', '收盘价', '吸筹值', 'PCR吸筹总仓位'列
    返回:
        pd.DataFrame: 添加了'卫星吸筹调整仓位', '吸筹买卖', '收益率'列的DataFrame
    """
    # 初始化变量
    P, X, sell_flag, xichou_flag = 0, 0, 0, 0
    df['卫星吸筹调整仓位'] = 0
    df['吸筹买卖'] = ''
    df['收益率'] = 0.0  # 初始化收益率列
    df['PCR吸筹总仓位'] = df['pcr_bbi总仓位'].astype(float)  # 转换为浮点数

    # 遍历数据
    for idx, row in df.iterrows():
        xichou = row['吸筹值']
        close = row['收盘价']
        dt = row['日期']
        
        # 买入逻辑
        if xichou > 80 and P == 0:
            if idx < len(df) - 1:
                P = df.loc[idx + 1, '收盘价']  # 下一日的收盘价作为买入价格
                X = 1 - df.loc[idx + 1, 'PCR吸筹总仓位']  # 计算卫星吸筹调整仓位
                df.loc[idx + 1, '卫星吸筹调整仓位'] = X  # 更新卫星吸筹调整仓位
                DATE = dt
                sell_flag = 0
                df.loc[idx, 'PCR吸筹总仓位'] = 1  # 更新PCR吸筹总仓位
                df.loc[idx, '吸筹买卖'] = '买入'
                print(f'{dt}买入，价格：{P}')
            else:
                print(f"警告：最后一行数据无法执行买入吸筹买卖，因为没有次日数据。")
            continue
        
        # 继承前一天的PCR吸筹总仓位
        if idx > 0 and not df.loc[idx, '吸筹买卖'] and not df.loc[idx, 'pcr_bbi仓位调整']:
            df.loc[idx, 'PCR吸筹总仓位'] = df.loc[idx - 1, 'PCR吸筹总仓位']
        elif df.loc[idx,'pcr_bbi仓位调整'] and 0<df.loc[idx - 1, 'PCR吸筹总仓位']<1:
            df.loc[idx, 'PCR吸筹总仓位'] = df.loc[idx - 1, 'PCR吸筹总仓位']+df.loc[idx, 'pcr_bbi仓位调整']
        elif df.loc[idx,'pcr_bbi仓位调整']==-0.1 and df.loc[idx - 1, 'PCR吸筹总仓位']==0:
            df.loc[idx, 'PCR吸筹总仓位']=0
        elif df.loc[idx,'pcr_bbi仓位调整']==0.1 and df.loc[idx - 1, 'PCR吸筹总仓位']==1:
            df.loc[idx, 'PCR吸筹总仓位']=1

        return_pct=0
        ##收益率再看，因为好像就是0.08和0.1
        # 卖出逻辑
        if P != 0 and X > 0:  # 确保有买入价格且有持仓
            if  close >= P * 1.1 and sell_flag != 2:  
                sell_amount = X
                df.loc[idx, 'PCR吸筹总仓位'] -= sell_amount
                X = 0
                sell_flag = 2
                P = 0
                return_pct=10
                df.loc[idx, '吸筹买卖'] = f'卖出{sell_amount}'
                print(f'P达到1.1,{dt}卖出，卖出仓位：{sell_amount}，收益率：{return_pct:.2f}%')
            elif close >= P * 1.08 and sell_flag == 0:  
                sell_amount = 0.5 * X
                df.loc[idx, 'PCR吸筹总仓位'] -= sell_amount
                X -= sell_amount
                sell_flag = 1
                df.loc[idx, '吸筹买卖'] = f'卖出{sell_amount}'
                return_pct=8
                print(f'P达到1.08{dt}卖出，卖出仓位：{sell_amount}，收益率：{return_pct:.2f}%')
            elif CD(df, DATE.date(), dt.date(), '日期') > 60:  # 超时卖出
                sell_amount = X
                df.loc[idx, 'PCR吸筹总仓位'] -= sell_amount
                X = 0
                sell_flag = 2
                return_pct=(df.loc[idx, '收盘价']-P)/P*100
                P = 0
                df.loc[idx, '吸筹买卖'] = f'自动止盈或止损{sell_amount}'
                df.loc[idx, '收益率'] = return_pct
                print(f'{dt}自动止盈或止损，卖出仓位：{sell_amount}，收益率：{return_pct:.2f}%')
    
    return df