import pandas as pd
from datetime import timedelta
import numpy as np
import os
from tradeday import count_tradeday as CD


from pcr_bbi_new import analyze_market_data 
from xichou_fun import xichou

from cross import find_cross_under
from cross import add_weekday_column
from function_new import function

from API import API
from husen_new import analyze_market_signals_with_position as hs3
from sum import sum

from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.utils import get_column_letter

from color import color

if __name__ == "__main__":

    # 替换为你的文件路径
    input_excel_file = r"D:\apps\中金项目\7-29-收益率\mian7月31日\main1\main\resource\resource.xlsx"
    input_excel_file2 = r"D:\apps\中金项目\7-29-收益率\mian7月31日\main1\main\resource\husen.xlsx"
    output_excel_file = r"D:\apps\中金项目\7-29-收益率\mian7月31日\main1\main\result\result_color.xlsx"
    initial_pos = 0.7

    processed_df = analyze_market_data(input_excel_file, date_column='日期', position=initial_pos)
    df=xichou(processed_df)
    df=function(df)
    
    week_df=hs3(input_excel_file2)
    df=API(df,week_df)

    df=sum(df,['吸筹总仓位','振幅指标仓位','周度bbi仓位调整'])
    styled_df = df.style.apply(color, axis=None)

    # 保存到 Excel（颜色可能需要特定库支持，如 openpyxl）
    styled_df.to_excel(output_excel_file , engine='openpyxl', index=False)

    print("已生成带颜色的 Excel 文件：styled_output.xlsx")
