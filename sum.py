import pandas as pd

def sum(df, col_names, output_col='组合总仓位'):
    """
    将指定列的浮点数数据求和，添加到新列中，处理缺失值。
    
    参数:
    df (pandas.DataFrame): 输入的DataFrame
    col_names (list): 需要求和的列名列表（长度应为3）
    output_col (str): 输出列名，默认为'sum'
    
    返回:
    pandas.DataFrame: 增加了输出列的DataFrame
    """
    # 验证列名是否存在
    if not all(col in df.columns for col in col_names):
        raise ValueError("指定的列名中有不存在的列")
    # 验证列数
    if len(col_names) != 3:
        raise ValueError("请提供正好4个列名")
    
    # 处理缺失值并转换为浮点数
    for col in col_names:
        # 将列转换为浮点数，缺失值保留为NaN
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # 求和，忽略NaN
    df[output_col] = df[col_names].sum(axis=1, skipna=True)

    return df