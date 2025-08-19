import pandas as pd
import os
import traceback
from datetime import timedelta

def analyze_market_signals_with_position(input_file_path, date_column='日期'):
    """
    根据周度策略分析市场数据，生成交易信号并计算仓位变化。
    核心规则：
    1. 买入信号：BBI上穿后设置标记价，价格达到标记价后触发预警，5周内满足MACD条件则在下一周周五买入。
       - MACD条件: MACD > 0
       - 仓位调整: +15%
    2. 卖出信号：BBI下穿，在下一周周五卖出。
       - 仓位调整: -15%
    3. 仓位限制：总仓位在0%到100%之间。

    参数:
    input_file_path (str): 输入Excel/CSV文件的路径。
    date_column (str): Excel/CSV文件中表示日期的列名，默认为'日期'。

    返回:
    pd.DataFrame: 包含交易信号和仓位调整的DataFrame。
    """
    try:
        # 读取文件
        file_extension = os.path.splitext(input_file_path)[1].lower()
        if file_extension == '.xlsx':
            df_weekly = pd.read_excel(input_file_path)
        elif file_extension == '.csv':
            df_weekly = pd.read_csv(input_file_path, encoding='utf-8-sig')
        else:
            print(f"错误: 不支持的文件类型 '{file_extension}'。请提供 .xlsx 或 .csv 文件。")
            return pd.DataFrame()

        # 检查所需列
        required_weekly_columns = [date_column, '周收盘价', '周度BBI', 'MACD']
        for col in required_weekly_columns:
            if col not in df_weekly.columns:
                print(f"错误: 输入文件中缺少必要的列 '{col}'。请检查列名。")
                return pd.DataFrame()

        # 转换日期列为日期时间格式并排序
        df_weekly[date_column] = pd.to_datetime(df_weekly[date_column])
        df_weekly = df_weekly.set_index(date_column).sort_index()

        # 初始化信号和仓位相关列
        df_weekly['BBI信号'] = ''
        df_weekly['MACD信号'] = ''
        df_weekly['周度bbi调整仓位'] = 0.0
        df_weekly['备注'] = ''

        # 状态变量
        buy_mark_price = None
        buy_warning_triggered = False
        warning_week_index = -1
        total_position = 0.0  # 跟踪当前总仓位
        pending_buy = False  # 标记是否有待执行的买入
        pending_sell = False  # 标记是否有待执行的卖出

        print("\n--- 开始生成交易信号和计算仓位 ---")
        # 遍历周度数据
        for i in range(1, len(df_weekly)):
            current_friday_date_obj = df_weekly.index[i]
            prev_friday_date_obj = df_weekly.index[i - 1]

            # 验证日期是否为周五
            if current_friday_date_obj.weekday() != 4:  # 4 表示周五
                df_weekly.loc[current_friday_date_obj, '备注'] = '非周五，跳过交易'
                continue

            # 提取当前和上一期数据
            current_close = df_weekly.loc[current_friday_date_obj, '周收盘价']
            prev_close = df_weekly.loc[prev_friday_date_obj, '周收盘价']
            current_bbi = df_weekly.loc[current_friday_date_obj, '周度BBI']
            prev_bbi = df_weekly.loc[prev_friday_date_obj, '周度BBI']
            current_macd = df_weekly.loc[current_friday_date_obj, 'MACD']

            # 信号过期逻辑
            if buy_warning_triggered and warning_week_index != -1 and (i - warning_week_index) > 5:
                buy_mark_price, buy_warning_triggered, warning_week_index = None, False, -1
                pending_buy = False

            # 处理待执行的买入或卖出（上一周触发的信号）
            if pending_buy and i < len(df_weekly):
                if total_position < 1.0:
                    adjustment = min(0.15, 1.0 - total_position)
                    total_position += adjustment
                    df_weekly.loc[current_friday_date_obj, '周度bbi调整仓位'] = adjustment
                    df_weekly.loc[current_friday_date_obj, '备注'] = '下一周周五买入'
                pending_buy = False
                buy_mark_price, buy_warning_triggered, warning_week_index = None, False, -1

            if pending_sell and i < len(df_weekly):
                if total_position > 0:
                    adjustment = -min(0.15, total_position)
                    total_position += adjustment
                    df_weekly.loc[current_friday_date_obj, '周度bbi调整仓位'] = adjustment
                    df_weekly.loc[current_friday_date_obj, '备注'] = '下一周周五卖出'
                pending_sell = False
                buy_mark_price, buy_warning_triggered, warning_week_index = None, False, -1

            # BBI上穿，设置标记价
            if prev_close < prev_bbi and current_close > current_bbi:
                df_weekly.loc[current_friday_date_obj, 'BBI信号'] = '上穿'
                buy_mark_price = current_close * 1.05
                buy_warning_triggered, warning_week_index = False, -1

            # 价格达到标记价，触发预警
            if buy_mark_price is not None and not buy_warning_triggered and current_close >= buy_mark_price:
                buy_warning_triggered, warning_week_index = True, i

            # 预警后5周内，检查MACD条件以触发买入（下一周周五执行）
            if buy_warning_triggered and warning_week_index != -1 and (i - warning_week_index) <= 5:
                if current_macd > 0:
                    df_weekly.loc[current_friday_date_obj, 'MACD信号'] = '满足买入条件'
                    pending_buy = True  # 标记为下一周周五买入

            # BBI下穿，触发卖出（下一周周五执行）
            if prev_close >= prev_bbi and current_close < current_bbi:
                df_weekly.loc[current_friday_date_obj, 'BBI信号'] = '下穿'
                pending_sell = True  # 标记为下一周周五卖出
                buy_mark_price, buy_warning_triggered, warning_week_index = None, False, -1

        print("--- 信号生成和仓位计算完毕 ---")

        # 恢复日期列为普通列
        df_weekly = df_weekly.reset_index()

        return df_weekly

    except Exception as e:
        print(f"发生严重错误: {e}")
        traceback.print_exc()
        return pd.DataFrame()

if __name__ == "__main__":
    # --- 配置区 ---
    inputfile = r"D:\apps\中金项目\7-29-收益率\mian7月31日\main1\main\resource\husen.xlsx"
    outputfile = r'D:\apps\中金项目\7-29-收益率\mian7月31日\main1\main\result\husen.xlsx'
    # --- 运行策略 ---
    print(f"正在读取文件: {inputfile}")
    processed_df = analyze_market_signals_with_position(inputfile, date_column='日期')

    if not processed_df.empty:
        # 调整列顺序以便查看
        cols = ['日期', '周收盘价', '周度BBI', 'MACD', 'BBI信号', 'MACD信号', '周度bbi调整仓位', '备注']
        processed_df = processed_df[[c for c in cols if c in processed_df.columns]]
        processed_df.to_excel(outputfile, index=False)
        print(f"\n处理完成。包含收益分析结果的新数据已保存到: {outputfile}")
    else:
        print("\n数据处理失败或未找到有效数据，未生成输出文件。")