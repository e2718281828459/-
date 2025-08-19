import pandas as pd

def color(df):
    """
    为 DataFrame 中的指定单元格设置字体颜色，基于以下规则：
    1. 持仓量PCR百分位 > 90% 且 持仓量PCR > 100%：'持仓量PCR百分位' 和 '持仓量PCR' 字体为红色。
    2. 持仓量PCR百分位 < 15%：'持仓量PCR百分位' 字体为绿色。
    3. 吸筹值 > 80：'吸筹值' 字体为蓝色。
    4. 振幅 > 2.5% 且 涨跌幅 < 0：'振幅(%)' 和 '涨跌幅(%)' 字体为橙色。

    参数:
    df (pd.DataFrame): 输入的 DataFrame，包含相关列。

    返回:
    pd.DataFrame: 应用了颜色样式的 DataFrame（样式为 HTML 格式）。
    """
    # 检查所需列是否存在
    required_columns = ['持仓量PCR百分位', '持仓量PCR', '吸筹值', '振幅(%)', '涨跌幅(%)']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"缺少必要的列: {missing_columns}")

    # 创建样式 DataFrame，初始化为空字符串
    styles = pd.DataFrame('', index=df.index, columns=df.columns)

    # 规则 1: 持仓量PCR百分位 > 90% 且 持仓量PCR > 100%，字体红色
    condition1 = (df['持仓量PCR百分位'] > 0.9) & (df['持仓量PCR'] > 1.0)
    styles.loc[condition1, '持仓量PCR百分位'] = 'color: red'
    styles.loc[condition1, '持仓量PCR'] = 'color: red'

    # 规则 2: 持仓量PCR百分位 < 15%，字体绿色
    condition2 = df['持仓量PCR百分位'] < 0.15
    styles.loc[condition2, '持仓量PCR百分位'] = 'color: green'

    # 规则 3: 吸筹值 > 80，字体蓝色
    condition3 = df['吸筹值'] > 80
    styles.loc[condition3, '吸筹值'] = 'color: blue'

    # 规则 4: 振幅 > 2.5% 且 涨跌幅 < 0，字体橙色
    condition4 = (df['振幅(%)'] > 0.025) & (df['涨跌幅(%)'] < 0)
    styles.loc[condition4, '振幅(%)'] = 'color: orange'
    styles.loc[condition4, '涨跌幅(%)'] = 'color: orange'

    return styles