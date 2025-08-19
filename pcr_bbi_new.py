import pandas as pd
import numpy as np
import pandas as pd
import os  # 导入os模块，用于文件路径操作
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.utils import get_column_letter


def process_trade_signals(df, sell_bands, buy_bands, date_column='日期'):
    """
    处理买卖信号，根据BBI下穿/上穿确定卖出/买入000852.SH。
    规则：
    - 下穿/上穿发生在周一或周二 -> 当周周五卖出/买入
    - 下穿/上穿发生在周三、周四或周五 -> 下周周五卖出/买入
    参数：
    - df: DataFrame，包含000852.SH、收盘价、日度BBI等列
    - sell_bands: 卖出波段的起始和结束索引列表 [(start_idx, end_idx), ...]
    - buy_bands: 买入波段的起始和结束索引列表 [(start_idx, end_idx), ...]
    - date_column: 000852.SH列名，默认为'日期'
    返回：
    - potential_sell_fridays: 卖出000852.SH集合
    - potential_buy_fridays: 买入000852.SH集合
    """
    potential_sell_fridays = set()
    potential_buy_fridays = set()

    # 确保000852.SH列为 datetime 类型
    df[date_column] = pd.to_datetime(df[date_column])

    # 处理卖出波段：查找每个波段后的第一个BBI下穿信号
    for band_start_idx, band_end_idx in sell_bands:
        for i in range(band_start_idx, min(band_end_idx + 1, len(df) - 1)):
            # 检查BBI下穿：当前收盘价 >= BBI，下一交易日收盘价 < BBI
            if df.loc[i, '收盘价'] >= df.loc[i, '日度BBI'] and df.loc[i + 1, '收盘价'] < df.loc[i + 1, '日度BBI']:
                crossover_date_obj = df.loc[i + 1, date_column]  # 下穿发生000852.SH
                crossover_weekday = crossover_date_obj.weekday()  # 0=周一, 4=周五

                # 根据星期确定卖出000852.SH
                if crossover_weekday in [0, 1]:  # 周一或周二
                    sell_date = crossover_date_obj + pd.offsets.Week(weekday=4)  # 当周周五
                else:  # 周三、周四、周五
                    sell_date = crossover_date_obj + pd.offsets.Week(weekday=4) + pd.offsets.Week(1)  # 下周周五

                # 确保卖出000852.SH在数据范围内
                if sell_date in df[date_column].values:
                    potential_sell_fridays.add(sell_date.date())
                break  # 找到第一个下穿信号后，跳出循环

    # 处理买入波段：查找每个波段后的第一个BBI上穿信号
    for band_start_idx, band_end_idx in buy_bands:
        for i in range(band_start_idx, min(band_end_idx + 1, len(df) - 1)):
            # 检查BBI上穿：当前收盘价 < BBI，下一交易日收盘价 > BBI
            if df.loc[i, '收盘价'] < df.loc[i, '日度BBI'] and df.loc[i + 1, '收盘价'] > df.loc[i + 1, '日度BBI']:
                crossover_date_obj = df.loc[i + 1, date_column]  # 上穿发生000852.SH
                crossover_weekday = crossover_date_obj.weekday()  # 0=周一, 4=周五

                # 根据星期确定买入000852.SH
                if crossover_weekday in [0, 1]:  # 周一或周二
                    buy_date = crossover_date_obj + pd.offsets.Week(weekday=4)  # 当周周五
                else:  # 周三、周四、周五
                    buy_date = crossover_date_obj + pd.offsets.Week(weekday=4) + pd.offsets.Week(1)  # 下周周五

                # 确保买入000852.SH在数据范围内
                if buy_date in df[date_column].values:
                    potential_buy_fridays.add(buy_date.date())
                break  # 找到第一个上穿信号后，跳出循环

    return potential_sell_fridays, potential_buy_fridays




def find_pcr_bands(df, pcr_condition_series, min_consecutive_days=3):
    """
    识别DataFrame中满足特定PCR条件的连续交易日波段。
    一个波段必须至少包含 min_consecutive_days 个连续交易日满足条件。

    参数:
    df (pd.DataFrame): 完整的DataFrame。
    pcr_condition_series (pd.Series): 布尔Series，表示每天是否满足PCR条件。
    min_consecutive_days (int): 构成有效波段所需的最小连续天数。

    返回:
    list: 包含 (start_idx, end_idx) 元组的列表，表示每个识别到的波段的起始和结束索引。
    """
    bands = []  # 存储识别到的所有波段的起始和结束索引
    i = 0  # 初始化循环变量，用于遍历DataFrame的每一行
    while i < len(df):  # 遍历所有数据
        if pcr_condition_series.iloc[i]:  # 如果当前交易日满足PCR条件
            band_start_idx = i  # 记录波段的起始索引
            j = i  # 初始化内部循环变量
            while j < len(df) and pcr_condition_series.iloc[j]:
                j += 1  # 向后查找，直到条件不满足或数据结束
            band_end_idx = j - 1  # 波段的结束索引是最后一个满足条件的000852.SH

            # 检查识别到的波段长度是否满足最小连续天数要求
            if (band_end_idx - band_start_idx + 1) >= min_consecutive_days:
                bands.append((band_start_idx, band_end_idx))  # 将有效波段添加到列表中
            i = j  # 将主循环的索引移动到当前波段结束的下一个位置，继续查找新波段
        else:
            i += 1  # 如果当前交易日不满足条件，则检查下一个
    return bands  # 返回所有识别到的波段


def analyze_market_data(input_file_path, date_column='日期', position=0.0, total_position_limit=1.0):
    """
    分析Excel/CSV文件中的市场数据，包括：
    1. 找出连续满足特定PCR卖出条件（持仓量PCR百分位 > 0.9 且 持仓量PCR > 1.0）的波段（至少3天）。
    2. 找出满足特定PCR买入条件（持仓量PCR百分位 < 0.15）的波段（至少1天）。
    3. 在每个卖出波段激活后，寻找第一个收盘价下穿日度BBI的信号，并执行卖出操作。每个波段只执行一次卖出。
       卖出在下穿日最近的周五执行（如果下穿发生在周五，则为下一个周五）。
    4. 在每个买入波段激活后，寻找第一个收盘价上穿日度BBI的信号，并执行买入操作。每个波段只执行一次买入。
       买入在上穿日最近的周五执行（如果上穿发生在周五，则为下一个周五）。
       上穿定义为：这一天收盘价小于BBI，下一天收盘价大于BBI。
    5. 在DataFrame中添加pcr_bbi仓位调整和pcr_bbi总仓位信息，并标记每个交易日所属的PCR波段。
    6. 新增规则：一个交易周内只能进行一次加仓或减仓，如果一周出现多个信号，卖出优先。
    7. 新增规则：pcr_bbi总仓位上限为1.0（100%），下限为0。

    参数:
    input_file_path (str): 输入Excel/CSV文件的路径。
    date_column (str): Excel/CSV文件中表示000852.SH的列名，默认为'日期'。
    position (float): 初始仓位，必须在0到1之间。
    total_position_limit (float): pcr_bbi总仓位的上限，默认为1.0。

    返回:
    pd.DataFrame: 包含原始数据、新增的'pcr_bbi仓位调整'、'pcr_bbi总仓位'、'PCR_BBI卖出预警'和'PCR_BBI买入预警'列的DataFrame。
                  如果发生错误，则返回空的DataFrame。
    """
    try:
        # 验证初始仓位是否在有效范围内
        if not (0 <= position <= total_position_limit):
            print(f"错误: 初始仓位 ({position}) 必须在 0 和 {total_position_limit} 之间。")
            return pd.DataFrame()

        # 根据文件扩展名确定文件类型并读取
        file_extension = os.path.splitext(input_file_path)[1].lower()
        if file_extension == '.xlsx':
            df = pd.read_excel(input_file_path)
        elif file_extension == '.csv':
            df = pd.read_csv(input_file_path)
        else:
            print(f"错误: 不支持的文件类型 '{file_extension}'。请提供 .xlsx 或 .csv 文件。")
            return pd.DataFrame()

        required_columns = [date_column, '持仓量PCR百分位', '持仓量PCR', '收盘价', '日度BBI']
        for col in required_columns:
            if col not in df.columns:
                print(f"错误: 输入文件中缺少必要的列 '{col}'。请检查列名。")
                return pd.DataFrame()

        df[date_column] = pd.to_datetime(df[date_column])
        df = df.sort_values(by=date_column).reset_index(drop=True)
        df['持仓量PCR'] = df['持仓量PCR'].astype(str).str.replace('%', '', regex=False).astype(float)

        # --- 初始化新增列 ---
        df['pcr_bbi仓位调整'] = 0.0
        df['pcr_bbi总仓位'] = 0.0  # 临时初始化，后续会填充
        df['PCR_BBI卖出预警'] = None
        df['PCR_BBI买入预警'] = None


        # --- 1. 识别PCR卖出和买入波段 ---
        pcr_sell_condition = (df['持仓量PCR百分位'] > 0.9) & (df['持仓量PCR'] > 1.0)
        pcr_buy_condition = (df['持仓量PCR百分位'] < 0.15)
        sell_bands = find_pcr_bands(df, pcr_sell_condition, min_consecutive_days=3)
        buy_bands = find_pcr_bands(df, pcr_buy_condition, min_consecutive_days=1)

        # 在DataFrame中标记卖出波段ID
        for i, (start_idx, end_idx) in enumerate(sell_bands):
            df.loc[start_idx:end_idx, 'PCR_BBI卖出预警'] = f'SellBand_{i + 1}'
        # 在DataFrame中标记买入波段ID
        for i, (start_idx, end_idx) in enumerate(buy_bands):
            df.loc[start_idx:end_idx, 'PCR_BBI买入预警'] = f'BuyBand_{i + 1}'

        if sell_bands:
            print("--- 已识别到以下PCR卖出波段 ---")
            for i, (start_idx, end_idx) in enumerate(sell_bands):
                print(
                    f"波段 {i + 1}: 从 {df.loc[start_idx, date_column].strftime('%Y-%m-%d')} 到 {df.loc[end_idx, date_column].strftime('%Y-%m-%d')}")
        else:
            print("没有找到满足条件的PCR卖出波段。")

        if buy_bands:
            print("\n--- 已识别到以下PCR买入波段 ---")
            for i, (start_idx, end_idx) in enumerate(buy_bands):
                print(
                    f"波段 {i + 1}: 从 {df.loc[start_idx, date_column].strftime('%Y-%m-%d')} 到 {df.loc[end_idx, date_column].strftime('%Y-%m-%d')}")
        else:
            print("没有找到满足条件的PCR买入波段。")

        # --- 2. BBI交易信号分析 ---
        potential_sell_fridays = set()
        potential_buy_fridays = set()
        potential_sell_fridays, potential_buy_fridays=process_trade_signals(df, sell_bands, buy_bands, date_column='日期')

        # --- 3. 应用周度调整和pcr_bbi总仓位限制 ---
        final_trade_actions_by_friday = {}
        # 优先处理卖出信号
        for sell_friday in sorted(list(potential_sell_fridays)):
            final_trade_actions_by_friday[sell_friday] = -0.10
        # 再处理买入信号
        for buy_friday in sorted(list(potential_buy_fridays)):
            if buy_friday not in final_trade_actions_by_friday:
                final_trade_actions_by_friday[buy_friday] = 0.10

        sell_signals_for_print = []
        buy_signals_for_print = []
        skipped_signals_for_print = []

        current_position = position  # 使用传入的初始仓位
        for idx in range(len(df)):
            current_date_in_df = df.loc[idx, date_column].date()

            if current_date_in_df in final_trade_actions_by_friday:
                adjustment_value = final_trade_actions_by_friday[current_date_in_df]
                actual_adjustment = 0

                if adjustment_value > 0:  # 尝试加仓
                    if current_position < total_position_limit:
                        # 计算实际可加仓位，确保不超过上限
                        actual_adjustment = min(adjustment_value, total_position_limit - current_position)
                        buy_signals_for_print.append({
                            '操作000852.SH': current_date_in_df.strftime('%Y-%m-%d'),
                            '类型': '加仓',
                            '调整幅度': actual_adjustment
                        })
                    else:
                        skipped_signals_for_print.append(
                            f"跳过操作: 000852.SH {current_date_in_df.strftime('%Y-%m-%d')}，尝试加仓但pcr_bbi总仓位已达上限 {current_position:.0%}")

                elif adjustment_value < 0:  # 尝试减仓
                    if current_position > 0:
                        # 计算实际可减仓位，确保不低于0
                        actual_adjustment = max(adjustment_value, -current_position)
                        sell_signals_for_print.append({
                            '操作000852.SH': current_date_in_df.strftime('%Y-%m-%d'),
                            '类型': '减仓',
                            '调整幅度': actual_adjustment
                        })
                    else:
                        skipped_signals_for_print.append(
                            f"跳过操作: 000852.SH {current_date_in_df.strftime('%Y-%m-%d')}，尝试减仓但pcr_bbi总仓位已为0")

                # 更新pcr_bbi仓位调整列和pcr_bbi总仓位
                df.loc[idx, 'pcr_bbi仓位调整'] = actual_adjustment
                current_position += actual_adjustment
                current_position = round(current_position, 2)  # 避免浮点数精度问题

            # 记录每一天的pcr_bbi总仓位
            df.loc[idx, 'pcr_bbi总仓位'] = current_position

        if sell_signals_for_print:
            print("\n--- 已识别到以下最终卖出操作 ---")
            for signal in sell_signals_for_print:
                print(
                    f"操作000852.SH: {signal['操作000852.SH']}, 类型: {signal['类型']}, 调整幅度: {signal['调整幅度'] * 100:.0f}%")

        if buy_signals_for_print:
            print("\n--- 已识别到以下最终买入操作 ---")
            for signal in buy_signals_for_print:
                print(
                    f"操作000852.SH: {signal['操作000852.SH']}, 类型: {signal['类型']}, 调整幅度: {signal['调整幅度'] * 100:.0f}%")

        if skipped_signals_for_print:
            print("\n--- 以下操作因pcr_bbi总仓位限制被跳过或调整 ---")
            for note in skipped_signals_for_print:
                print(note)

        if not sell_signals_for_print and not buy_signals_for_print and not skipped_signals_for_print:
            print("\n在此期间没有执行任何pcr_bbi仓位调整操作。")

        return df

    except FileNotFoundError:
        print(f"错误: 文件未找到，请检查路径: {input_file_path}")
        return pd.DataFrame()
    except Exception as e:
        print(f"发生错误: {e}")
        return pd.DataFrame()


if __name__ == "__main__":
    # 替换为你的文件路径
    input_excel_file = r"D:\apps\中金项目\7-29-收益率\mian7月31日\main_color\code\副本中证1000.xlsx"
    # 新的输出文件路径
    output_excel_file = r"D:\apps\中金项目\7-29-收益率\mian7月31日\main_color\code\中证1000result.xlsx"

    initial_pos = 0.7
    df = analyze_market_data(input_excel_file, date_column='日期', position=initial_pos)

    if not df.empty:
        df.to_excel(output_excel_file)
        print(f"\n处理完成。使用 {initial_pos:.0%} 的初始仓位，分析结果已保存到: {output_excel_file}")
    else:
        print("\n数据处理失败或未找到有效数据，未生成输出文件。")
