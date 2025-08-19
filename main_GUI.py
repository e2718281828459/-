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

import argparse

from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox
import sys
import os

from color import color

def main(input_excel_file,input_excel_file2,output_excel_file,initial_pos):
    
    processed_df = analyze_market_data(input_excel_file, date_column='日期', position=initial_pos)
    df=xichou(processed_df)
    df=function(df)
    
    week_df=hs3(input_excel_file2)
    df=API(df,week_df)

    df=sum(df,['PCR吸筹总仓位','振幅指标调整仓位','周度bbi调整仓位'])
    
    
    df_new = df[["日期",'持仓量PCR百分位', '持仓量PCR', '吸筹值', '振幅(%)', '涨跌幅(%)',"pcr_bbi总仓位","PCR_BBI卖出预警","卫星吸筹调整仓位",'收益率',"PCR吸筹总仓位","振幅距离预警的日期","振幅指标调整仓位","振幅卖出指标","周度bbi调整仓位","备注","组合总仓位"]]

    styled_df = df_new.style.apply(color, axis=None)
    
    
    # 保存到 Excel（颜色可能需要特定库支持，如 openpyxl）
    styled_df.to_excel(output_excel_file , engine='openpyxl', index=False)



#这一整个部分都是GUI
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("参数输入 GUI")
        self.setGeometry(100, 100, 500, 400)

        # 输入文件路径 1
        self.label1 = QLabel("日表文件:", self)
        self.label1.move(20, 20)
        self.input1 = QLineEdit(self)
        self.input1.setGeometry(120, 20, 300, 30)
        self.browse_btn1 = QPushButton("浏览", self)
        self.browse_btn1.setGeometry(430, 20, 60, 30)
        self.browse_btn1.clicked.connect(self.browse_input1)

        # 输入文件路径 2
        self.label2 = QLabel("周表文件:", self)
        self.label2.move(20, 60)
        self.input2 = QLineEdit(self)
        self.input2.setGeometry(120, 60, 300, 30)
        self.browse_btn2 = QPushButton("浏览", self)
        self.browse_btn2.setGeometry(430, 60, 60, 30)
        self.browse_btn2.clicked.connect(self.browse_input2)

        # 输出文件路径
        self.label3 = QLabel("输出文件路径:", self)
        self.label3.move(20, 100)
        self.output = QLineEdit(self)
        self.output.setGeometry(120, 100, 300, 30)
        self.browse_btn3 = QPushButton("浏览", self)
        self.browse_btn3.setGeometry(430, 100, 60, 30)
        self.browse_btn3.clicked.connect(self.browse_output)

        # 初始仓位输入框
        self.label4 = QLabel("初始仓位参数:", self)  # 修改标签
        self.label4.move(20, 140)
        self.float_input = QLineEdit(self)  # 修改变量名
        self.float_input.setGeometry(120, 140, 300, 30)
        self.float_input.setPlaceholderText("请输入一个初始仓位（例如 3.14）")  # 更新提示

        # 运行按钮
        self.run_btn = QPushButton("运行", self)
        self.run_btn.setGeometry(120, 200, 100, 40)
        self.run_btn.clicked.connect(self.run_script)

    def browse_input1(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择日表文件", "", "All Files (*);;Text Files (*.txt);;CSV Files (*.csv)")
        if file_path:
            self.input1.setText(file_path)

    def browse_input2(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择周表文件", "", "All Files (*);;Text Files (*.txt);;CSV Files (*.csv)")
        if file_path:
            self.input2.setText(file_path)

    def browse_output(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "选择输出文件", "", "Text Files (*.txt);;All Files (*)")
        if file_path:
            self.output.setText(file_path)

    def run_script(self):
        input1_path = self.input1.text()
        input2_path = self.input2.text()
        output_path = self.output.text()
        float_param_text = self.float_input.text()  # 修改变量名

        # 验证所有输入
        if not input1_path or not input2_path or not output_path or not float_param_text:
            QMessageBox.critical(self, "错误", "请填写所有输入文件路径、输出文件路径和初始仓位参数！")
            return

        # 验证初始仓位输入
        try:
            float_param = float(float_param_text)
        except ValueError:
            QMessageBox.critical(self, "错误", "初始仓位参数必须是一个有效的数字（例如 3.14）！")
            return

        result = main(input1_path, input2_path, output_path, float_param)
        
        QMessageBox.information(self, "成功", f"处理完成，结果已保存到 {output_path}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())