import pandas as pd

def API(daily_df, week_df):
    # 确保日期列是 datetime 类型
    daily_df['日期'] = pd.to_datetime(daily_df['日期'])
    week_df['日期'] = pd.to_datetime(week_df['日期'])

    # 创建新的 DataFrame 基于 daily_df
    new_daily_df = daily_df.copy()

    # 将 week_df 的日期作为参考
    week_dates = week_df['日期'].unique()

    # 遍历 week_df 的列（排除 '日期' 列），作为新列添加到 new_daily_df
    for column in week_df.columns:
        if column != '日期':
            # 根据列类型初始化，保留原始类型
            if week_df[column].dtype == 'object':  # 字符串列
                new_daily_df[column] = ''
            else:
                new_daily_df[column] = pd.NA

    # 填充 week_df 的数据到 new_daily_df
    for date in week_dates:
        mask = new_daily_df['日期'] == date
        if mask.any():
            week_row = week_df[week_df['日期'] == date].iloc[0].drop('日期')
            for col, value in week_row.items():
                # 根据列类型处理
                if pd.api.types.is_numeric_dtype(week_df[col].dtype):
                    new_daily_df.loc[mask, col] = pd.to_numeric(value, errors='coerce')
                else:
                    new_daily_df.loc[mask, col] = value

    return new_daily_df