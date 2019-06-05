import sys
import os.path
import subprocess
import time
import datetime
import shutil
import unicodedata
import json
import pandas as pd
from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QApplication, QWidget, QVBoxLayout, QFormLayout, \
    QLabel, QLineEdit, QMessageBox, QTabWidget, QComboBox, QCheckBox, QTextEdit, QCompleter, QTableWidget, \
    QTableWidgetItem, QAbstractItemView, QFileDialog
from PyQt5.QtCore import pyqtSlot, QStringListModel
from PyQt5 import QtGui, QtCore
from pymongo import MongoClient


class dig_edit_situation(QWidget):  # 編輯情境
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        client = MongoClient("127.0.0.1", 27017)
        db = client.gossip
        self.collection = db.situations

        self.main_layout = QVBoxLayout()

        situation_widget = QFormLayout()
        self.select_layout = QHBoxLayout()

        self.search_text = QLineEdit()
        self.search_text.textChanged.connect(self.search_situations)

        self.tableWidget = QTableWidget()
        self.tableWidget.setRowCount(self.collection.find().count())
        self.tableWidget.setColumnCount(1)
        self.tableWidget.itemSelectionChanged.connect(self.show_selected_item)
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.horizontalHeader().setVisible(False)

        self.situation_index_list = []
        self.search_situations()
        self.tableWidget.resizeColumnsToContents()

        self.new_or_not = QCheckBox('新增情境')
        self.new_or_not.stateChanged.connect(self.state_changed)

        self.remove_btn = QPushButton('刪除情境')
        self.remove_btn.clicked.connect(self.remove_btn_method)

        self.select_layout.addWidget(self.search_text)
        self.select_layout.addWidget(self.new_or_not)
        self.select_layout.addWidget(self.remove_btn)
        self.situation = QTextEdit()
        self.events = QTextEdit()


        situation_widget.addRow(QLabel('搜尋'), self.select_layout)
        situation_widget.addRow(QLabel('欲編輯情境'), self.tableWidget)
        situation_widget.addRow(QLabel('情境'), self.situation)
        situation_widget.addRow(QLabel('連續事件'), self.events)

        button_layout = QHBoxLayout()
        save_btn = QPushButton("儲存")
        save_btn.clicked.connect(self.save_btn_method)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.cancel_btn_method)

        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)

        self.main_layout.addLayout(situation_widget)
        self.main_layout.addLayout(button_layout)

        self.setLayout(self.main_layout)

    # 好像有BUG，會拿到下一句
    @pyqtSlot()
    def show_selected_item(self):
        if len(self.situation_index_list) > 0:
            print(self.tableWidget.currentIndex().row())
            data = self.collection.find_one({'Situation': self.situation_index_list[
                min(self.tableWidget.currentIndex().row(),
                    len(self.situation_index_list) - 1)]})
            if data != None:
                self.situation.setText(str(data['Situation']))
                self.events.setText('\n'.join(data['Events']))
        else:
            pass

    @pyqtSlot()
    def search_situations(self):
        self.tableWidget.clear()
        self.situation_index_list.clear()

        if not self.search_text.text() == '':
            search_condition = [{'Situation': {'$regex': '{0}'.format(word)}}
                                for word in self.search_text.text().split()]
            search = self.collection.find({'$and': search_condition})
            self.tableWidget.setRowCount(search.count())

            for index, item in enumerate(search):
                self.tableWidget.setItem(index, 0, QTableWidgetItem(str(item['Situation'])))
                self.situation_index_list.append(item['Situation'])

        else:
            search = self.collection.find()
            self.tableWidget.setRowCount(search.count())
            for index, item in enumerate(search):
                self.tableWidget.setItem(index, 0, QTableWidgetItem(str(item['Situation'])))
                self.situation_index_list.append(item['Situation'])



    # finished
    @pyqtSlot()
    def state_changed(self):
        self.situation.clear()
        self.events.clear()
        if self.new_or_not.checkState():
            self.tableWidget.setDisabled(True)

        else:
            self.tableWidget.setDisabled(False)

    # 清除最後一個好像有BUG
    # 已解決: 最後一個被刪除後會留下一個空的string
    @pyqtSlot()
    def remove_btn_method(self):
        if self.tableWidget.currentItem() is not None:
            if self.new_or_not.checkState():
                QMessageBox.information(self, "提醒", '請先勾去"新增情境"')

            elif len(self.situation_index_list) > 0:
                result = QMessageBox.question(self, '警告', '確定要刪除"{0}"嗎?'.format(self.tableWidget.currentItem().text()),
                                              QMessageBox.Yes | QMessageBox.No,
                                              QMessageBox.No)

                if result == QMessageBox.Yes:
                    data = self.situation_index_list[self.tableWidget.currentIndex().row()]
                    self.collection.remove({'Situation': data})

                    del self.situation_index_list[self.tableWidget.currentIndex().row()]

                    if self.tableWidget.rowCount() == 1:
                        self.tableWidget.setItem(0, 0, QTableWidgetItem(''))

                    else:
                        self.tableWidget.removeRow(self.tableWidget.currentIndex().row())

                else:
                    pass

            else:
                pass
        else:
            pass

    # finished
    @pyqtSlot()
    def save_btn_method(self):
        if self.new_or_not.checkState():
            data = {'uuid': self.collection.find().count(), 'Situation': self.situation.toPlainText(),
                    'Events': self.events.toPlainText().split('\n')
                        }
            self.collection.insert(data)
            # print(len(self.situation_index_list))
            self.situation_index_list.append(data['Situation'])
            # print(len(self.situation_index_list))
            self.tableWidget.insertRow(self.tableWidget.rowCount())
            self.tableWidget.setItem(self.tableWidget.rowCount() - 1, 0, QTableWidgetItem(str(data['Situation'])))
            QMessageBox.information(self, "提醒", '已儲存"{}"'.format(self.situation.toPlainText()))

        elif len(self.situation_index_list) > 0:
            data = self.collection.find_one({'Situation': self.situation_index_list[self.tableWidget.currentIndex().row()]})
            data['Situation'] = self.situation.toPlainText()
            data['Events'] = self.events.toPlainText().split('\n')
            self.collection.save(data)
            self.tableWidget.setItem(self.tableWidget.currentIndex().row(), 0, QTableWidgetItem(str(data['Situation'])))
            QMessageBox.information(self, "提醒", '已儲存"{}"'.format(self.situation.toPlainText()))

        else:
            pass

    @pyqtSlot()
    def cancel_btn_method(self):
        self.search_text.clear()
        self.situation.clear()
        self.events.clear()

class dig_edit_conversation(QWidget):  # 編輯對話
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        client = MongoClient("127.0.0.1", 27017)
        db = client.gossip
        self.collection = db.sentences

        self.main_layout = QVBoxLayout()

        situation_widget = QFormLayout()
        self.select_layout = QHBoxLayout()

        self.search_text = QLineEdit()
        self.search_text.textChanged.connect(self.search_situations)

        self.tableWidget = QTableWidget()
        self.tableWidget.setRowCount(self.collection.find().count())
        self.tableWidget.setColumnCount(1)
        self.tableWidget.itemSelectionChanged.connect(self.show_selected_item)
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.horizontalHeader().setVisible(False)

        self.tableWidget2 = QTableWidget()
        self.tableWidget2.setColumnCount(1)
        self.tableWidget2.itemSelectionChanged.connect(self.show_selected_sentence)
        self.tableWidget2.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableWidget2.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableWidget2.verticalHeader().setVisible(False)
        self.tableWidget2.horizontalHeader().setVisible(False)

        self.situation_index_list = []
        self.sentence_index_list = []
        self.search_situations()
        self.tableWidget2.setColumnWidth(0,500)
        self.tableWidget.resizeColumnsToContents()
        

        self.new_or_not = QCheckBox('新增情境')
        self.new_or_not.stateChanged.connect(self.state_changed)

        self.remove_btn = QPushButton('刪除情境')
        self.remove_btn.clicked.connect(self.remove_btn_method)

        self.select_layout.addWidget(self.search_text)
        self.select_layout.addWidget(self.new_or_not)
        self.select_layout.addWidget(self.remove_btn)
        self.name = QTextEdit()
        self.sentence = QTextEdit()


        situation_widget.addRow(QLabel('搜尋'), self.select_layout)
        situation_widget.addRow(QLabel('欲編輯情境'), self.tableWidget)
        situation_widget.addRow(QLabel('情境所有語句'), self.tableWidget2)
        situation_widget.addRow(QLabel('說話者'), self.name)
        situation_widget.addRow(QLabel('對話語句'), self.sentence)

        button_layout = QHBoxLayout()
        save_btn = QPushButton("儲存")
        save_btn.clicked.connect(self.save_btn_method)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.cancel_btn_method)

        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)

        self.main_layout.addLayout(situation_widget)
        self.main_layout.addLayout(button_layout)

        self.setLayout(self.main_layout)

    # 好像有BUG，會拿到下一句
    @pyqtSlot()
    def show_selected_item(self):
        self.tableWidget2.clear()
        self.sentence_index_list.clear()
        if len(self.situation_index_list) > 0:
            print(self.tableWidget.currentIndex().row())
            data = self.collection.find({'Situation': self.situation_index_list[
                min(self.tableWidget.currentIndex().row(),
                    len(self.situation_index_list) - 1)]})
            self.tableWidget2.setRowCount(data.count())
            if data != None:
                for index, item in enumerate(data):
                    self.tableWidget2.setItem(index, 0, QTableWidgetItem(str(item['Sentence'])))
                    self.sentence_index_list.append(item['Sentence'])
        else:
            pass

    @pyqtSlot()
    def show_selected_sentence(self):
        if len(self.sentence_index_list) > 0:
            print(self.tableWidget.currentItem().text())
            data = self.collection.find_one({'Sentence': self.sentence_index_list[
                min(self.tableWidget2.currentIndex().row(),
                    len(self.sentence_index_list) - 1)]})
            if data != None:
                self.name.setText(str(data['Name']))
                self.sentence.setText(data['Sentence'])
                
        else:
            pass
    

    @pyqtSlot()
    def search_situations(self):
        self.tableWidget.clear()
        self.situation_index_list.clear()

        if not self.search_text.text() == '':
            search_condition = [{'Situation': {'$regex': '{0}'.format(word)}}
                                for word in self.search_text.text().split()]
            search = list(self.collection.find({'$and': search_condition}))
            search = sorted(set([x['Situation'] for x in search]))
            self.tableWidget.setRowCount(len(search))

            for index, item in enumerate(search):
                self.tableWidget.setItem(index, 0, QTableWidgetItem(str(item)))
                self.situation_index_list.append(item)

        else:
            search = list(self.collection.find({'Name':''}))
            search = sorted(set([x['Situation'] for x in search]))
            self.tableWidget.setRowCount(len(search))
            for index, item in enumerate(search):
                self.tableWidget.setItem(index, 0, QTableWidgetItem(str(item)))
                self.situation_index_list.append(item)



    # finished
    @pyqtSlot()
    def state_changed(self):
        self.name.clear()
        self.sentence.clear()
        if self.new_or_not.checkState():
            self.tableWidget.setDisabled(True)
            self.tableWidget2.setDisabled(True)
        else:
            self.tableWidget.setDisabled(False)
            self.tableWidget2.setDisabled(False)

    # 清除最後一個好像有BUG
    # 已解決: 最後一個被刪除後會留下一個空的string
    @pyqtSlot()
    def remove_btn_method(self):
        if self.tableWidget2.currentItem() is not None:
            if self.new_or_not.checkState():
                QMessageBox.information(self, "提醒", '請先勾去"新增情境"')

            elif len(self.sentence_index_list) > 0:
                result = QMessageBox.question(self, '警告', '確定要刪除"{0}"嗎?'.format(self.tableWidget2.currentItem().text()),
                                              QMessageBox.Yes | QMessageBox.No,
                                              QMessageBox.No)

                if result == QMessageBox.Yes:
                    data = self.sentence_index_list[self.tableWidget2.currentIndex().row()]
                    self.collection.remove({'Sentence': data})

                    del self.sentence_index_list[self.tableWidget2.currentIndex().row()]

                    if self.tableWidget2.rowCount() == 1:
                        self.tableWidget2.setItem(0, 0, QTableWidgetItem(''))

                    else:
                        self.tableWidget2.removeRow(self.tableWidget2.currentIndex().row())

                else:
                    pass

            else:
                pass
        else:
            pass

    # finished
    @pyqtSlot()
    def save_btn_method(self):
        if self.new_or_not.checkState():
            data = {'uuid': self.collection.find().count(), 'Situation': self.tableWidget.currentItem().text(),
                    'Sentence': self.sentence.toPlainText(), 'Name': self.name.toPlainText()
                        }
            self.collection.insert(data)
            self.sentence_index_list.append(data['Sentence'])
            self.tableWidget2.insertRow(self.tableWidget2.rowCount())
            self.tableWidget2.setItem(self.tableWidget2.rowCount() - 1, 0, QTableWidgetItem(str(data['Sentence'])))
            QMessageBox.information(self, "提醒", '已儲存"{}"'.format(self.sentence.toPlainText()))

        elif len(self.sentence_index_list) > 0:
            data = self.collection.find_one({'Sentence': self.sentence_index_list[self.tableWidget2.currentIndex().row()]})
            data['Name'] = self.name.toPlainText()
            data['Sentence'] = self.sentence.toPlainText().split('\n')
            self.collection.save(data)
            self.tableWidget2.setItem(self.tableWidget2.currentIndex().row(), 0, QTableWidgetItem(str(data['Sentence'])))
            QMessageBox.information(self, "提醒", '已儲存"{}"'.format(self.sentence.toPlainText()))

        else:
            pass

    @pyqtSlot()
    def cancel_btn_method(self):
        self.search_text.clear()
        self.name.clear()
        self.sentence.clear()

class dig_sentence_log(QWidget):  # 回答紀錄
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        client = MongoClient('localhost', 27017)
        db = client.gossip
        self.collection_log = db.logs
        self.collection_sen = db.sentences

        self.main_layout = QVBoxLayout()

        sentence_widget = QFormLayout()
        self.select_layout = QHBoxLayout()
        self.show_all_sentences = QCheckBox('顯示所有紀錄')
        self.show_all_sentences.stateChanged.connect(self.state_changed)
        self.sentences_id = []

        self.search_text = QLineEdit()
        self.search_text.textChanged.connect(self.search_sentences)

        self.tableWidget = QTableWidget()
        self.tableWidget.setRowCount(self.collection_log.find().count())
        self.tableWidget.setColumnCount(1)
        self.tableWidget.itemSelectionChanged.connect(self.show_selected_item)
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.horizontalHeader().setVisible(False)

        self.sentence_index_list = []
        self.search_sentences()

        self.tableWidget.resizeColumnsToContents()

        self.remove_btn = QPushButton('刪除紀錄')
        self.remove_btn.clicked.connect(self.remove_btn_method)

        self.select_layout.addWidget(self.search_text)
        self.select_layout.addWidget(self.show_all_sentences)
        self.select_layout.addWidget(self.remove_btn)

        temp = self.collection_log.find_one()
        self.sentence = QTextEdit()
        self.name = ''
        self.events = QTextEdit()
        if temp is not None:
            self.sentence.setText(str(temp['Sentence']))
            self.name = temp['Name']
            self.events.setText('、'.join([x['Action'] for x in temp['Actions']]))
        self.situation = QTextEdit()

        sentence_widget.addRow(QLabel('搜尋'), self.select_layout)
        sentence_widget.addRow(QLabel('對話紀錄'), self.tableWidget)
        sentence_widget.addRow(QLabel('對話'), self.sentence)
        sentence_widget.addRow(QLabel('連續事件'), self.events)
        sentence_widget.addRow(QLabel('情境'), self.situation)

        button_layout = QHBoxLayout()
        save_btn = QPushButton("儲存")
        save_btn.clicked.connect(self.save_btn_method)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.cancel_btn_method)

        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)

        self.main_layout.addLayout(sentence_widget)
        self.main_layout.addLayout(button_layout)

        self.setLayout(self.main_layout)

    @pyqtSlot()
    def search_sentences(self):
        self.tableWidget.clear()
        self.sentence_index_list.clear()
        search_condition = []

        if not self.search_text.text() == '':
            search_condition += [{'Sentence': {'$regex': '{0}'.format(word)}}
                                 for word in self.search_text.text().split()]

        if len(search_condition):
            search = self.collection_log.find({'$and': search_condition})
        else:
            search = self.collection_log.find()

        self.tableWidget.setRowCount(search.count())

        for index, item in enumerate(search):
            self.tableWidget.setItem(index, 0, QTableWidgetItem(str(item['Sentence'])))
            self.sentence_index_list.append(item['_id'])

    @pyqtSlot()
    def load_sentence(self):
        for _ in range(len(self.sentences_id)):
            self.log_list.removeItem(0)

        self.sentences_id = []

        if self.show_all_sentences.checkState():
            for row in self.collection_log.find():
                self.sentences_id.append(row['_id'])
                self.log_list.addItem(str(row['Sentence']))
            if self.log_list.count() > len(self.sentences_id):
                if len(self.sentences_id) > 0:
                    self.log_list.removeItem(0)

        else:
            for row in self.collection_log.find():
                self.sentences_id.append(row['_id'])
                self.log_list.addItem(str(row['Sentence']))

    @pyqtSlot()
    def show_selected_item(self):
        if len(self.sentence_index_list) > 0:
            data = self.collection_log.find_one({'_id': self.sentence_index_list[
                min(self.tableWidget.currentIndex().row(), len(self.sentence_index_list) - 1)]})

            if data != None:
                self.sentence.setText(str(data['Sentence']))
                self.events.setText('、'.join([x['Action'] for x in data['Actions']]))
                self.name = data['Name']

        else:
            pass

    @pyqtSlot()
    def state_changed(self):
        self.sentence.clear()
        self.events.clear()
        self.search_sentences()

    @pyqtSlot()
    def remove_btn_method(self):
        if self.tableWidget.currentItem() is not None:
            if len(self.sentence_index_list) > 0:
                result = QMessageBox.question(self, '警告', '確定要刪除"{0}"嗎?'.format(self.tableWidget.currentItem().text()),
                                              QMessageBox.Yes | QMessageBox.No,
                                              QMessageBox.No)

                if result == QMessageBox.Yes:
                    current_index = self.sentence_index_list[self.tableWidget.currentIndex().row()]
                    self.collection_log.remove({'_id': current_index})

                    del self.sentence_index_list[self.tableWidget.currentIndex().row()]

                    if self.tableWidget.rowCount() == 1:
                        self.tableWidget.setItem(0, 0, QTableWidgetItem(''))

                    else:
                        self.tableWidget.removeRow(self.tableWidget.currentIndex().row())

                else:
                    pass
            else:
                QMessageBox.information(self, '警告', '目前沒有句子')
        else:
            pass

    def remove_item_from_table(self):
        current_index = self.sentence_index_list[self.tableWidget.currentIndex().row()]
        self.collection_log.remove({'_id': current_index})

        del self.sentence_index_list[self.tableWidget.currentIndex().row()]

        if self.tableWidget.rowCount() == 1:
            self.tableWidget.setItem(0, 0, QTableWidgetItem(''))

        else:
            self.tableWidget.removeRow(self.tableWidget.currentIndex().row())

    @pyqtSlot()
    def save_btn_method(self):
        if len(self.sentence_index_list) > 0:
            temp = self.collection_sen.find_one()
            if temp is not None:
                temp['Sentence'].append(self.sentence.toPlainText())
                self.collection_sen.save(temp)
            else:
                data = {'uuid': self.collection_ori.find().count(), 'Sentence': self.sentence.toPlainText(),
                        'Situation': self.situation.toPlainText(), 'Name': self.name
                        }
                self.collection_sen.insert(data)

            QMessageBox.information(self, '提醒', '已儲存"{}"'.format(self.sentence.toPlainText()))
            self.remove_item_from_table()

        else:
            QMessageBox.information(self, '警告', '目前沒有句子')

    @pyqtSlot()
    def cancel_btn_method(self):
        data = self.collection_log.find_one({'_id': self.sentence_index_list[self.tableWidget.currentIndex().row()]})
        self.sentence.setText(str(data['Sentence']))
        self.events.setText('、'.join([x['Action'] for x in temp['Actions']]))


class back_up_window(QWidget):  # 備份與還原
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.main_layout = QVBoxLayout()

        self.backup_btn = QPushButton('備份')
        self.backup_btn.clicked.connect(self.backup)
        self.restore_btn = QPushButton('還原')
        self.restore_btn.clicked.connect(self.restore)
        self.export_excel = QPushButton('匯出excel')
        self.export_excel.clicked.connect(self.excel)

        self.main_layout.addWidget(self.backup_btn)
        self.main_layout.addWidget(self.restore_btn)
        self.main_layout.addWidget(self.export_excel)

        self.setLayout(self.main_layout)

    def backup(self):
        # subprocess.check_output(['mongodump', '-d', 'taroko', '-o', './backup/{}'.format(time.strftime(r'%Y-%m-%d'))])
        subprocess.call(['mongodump', '-d', 'gossip', '-o', './backup/{}'.format(time.strftime(r'%Y-%m-%d'))])

        with open(r'./data/backup_log.json', 'w', encoding='utf-8') as config:
            json.dump({'last_backup_date': time.strftime(r'%Y-%m-%d')}, config, indent=4, ensure_ascii=True,
                      sort_keys=True)

        QMessageBox.information(self, '提醒', '備份成功')

    def restore(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        dir_name = QFileDialog.getExistingDirectory(self)
        if dir_name:
            subprocess.call(['mongorestore', '-d', 'gossip', '--drop', dir_name])
            QMessageBox.information(self, '提醒', '還原成功')

    def excel(self):
        client = MongoClient('localhost', 27017)
        db = client.gossip
        self.collection_sen = db.sentences
        sentence = []
        situation = []

        for row in self.collection_sen.find():
            sentence.append(row['Sentence'])
            situation.append(row['Situation'])
        df = pd.DataFrame({'Situation': situation, 'Sentence': sentence})
        # writer = pd.ExcelWriter(os.path.join(os.environ['USERPROFILE'], 'Desktop/')+time.strftime('%Y_%m_%d_%H_%M')+'.xlsx', engine='xlsxwriter')
        writer = pd.ExcelWriter(os.path.join(os.getcwd(),'backup/') + time.strftime('%Y_%m_%d_%H_%M')+'.xlsx', engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Sheet1', index=False)
        writer.save()
        QMessageBox.information(self, '提醒', '匯出成功')

    @staticmethod
    def auto_backup():
        subprocess.call(['mongodump', '-d', 'taroko', '-o', './backup/{}'.format(time.strftime(r'%Y-%m-%d'))])

        with open(r'./data/backup_log.json', 'w', encoding='utf-8') as config:
            json.dump({'last_backup_date': time.strftime(r'%Y-%m-%d')}, config, indent=4, ensure_ascii=True,
                      sort_keys=True)


class QA_system_window(QTabWidget):  # 整個大介面
    def __init__(self, title, width=650, height=500):
        super().__init__()
        self.title = title
        self.width = width
        self.height = height
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setMinimumSize(self.width, self.height)
        self.resize(self.width, self.height)

        self.addTab(dig_edit_situation(), '編輯情境')
        self.addTab(dig_edit_conversation(), '編輯對話')
        self.addTab(dig_sentence_log(), '回答紀錄')
        self.addTab(back_up_window(), '備份與還原')

        # Show widget
        self.show()

        # with open(r'./data/backup_log.json', 'r', encoding='utf-8') as backup_date:
        #     last_date_json = json.load(backup_date)
        #     temp = time.strptime(last_date_json['last_backup_date'], '%Y-%m-%d')
        #     last_date = datetime.datetime(temp[0], temp[1], temp[2])
        #     datetime.datetime.now()

        # if (datetime.datetime.now() - last_date).days > 6:
        #     back_up_window.auto_backup()
        #     QMessageBox.information(self, '提醒', '自動備份成功')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setFont(QtGui.QFont('', 12))
    main_window = QA_system_window('問答編輯系統 (Situation Editing Tool)')
    sys.exit(app.exec_())
