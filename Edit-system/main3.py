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


class dig_similarity_word(QWidget):  # 編輯連續事件
    def __init__(self):
        super().__init__()
        self.current_index = None
        self.initUI()

    def initUI(self):
        # insert search
        # get synonym
        with(open(r'./data/continuous_event.json', 'r', encoding='utf-8')) as data:
            self.continuous_event = json.load(data)

        self.synonym_events = []
        for _, values in self.continuous_event.items():
            self.synonym_events.append(values)

        self.all_events = set(
            events for values in self.synonym_events for events in values)

        def find_synonym():
            events = self.word1.text()
            for index, values in enumerate(self.synonym_events):
                if events in values:
                    self.current_index = index
                    self.word2.setText('\n'.join(values))
                    break
            else:
                self.current_index = None

        self.main_layout = QVBoxLayout()

        keyword_widget = QFormLayout()
        self.word_layout = QHBoxLayout()
        self.word1 = QLineEdit()
        self.remove_btn = QPushButton('移除事件')
        self.remove_btn.clicked.connect(self.remove_btn_method)

        def init_current_index():
            self.current_index = None
            find_synonym()
            if self.current_index is None:
                self.word2.clear()
            # print(self.current_index)

        self.word1.textEdited.connect(init_current_index)

        self.model = QStringListModel()
        self.model.setStringList(self.all_events)
        completer = QCompleter()
        completer.setModel(self.model)
        completer.activated.connect(find_synonym)
        self.word1.setCompleter(completer)

        self.word_layout.addWidget(self.word1)
        self.word_layout.addWidget(self.remove_btn)

        self.word2 = QTextEdit()

        keyword_widget.addRow(QLabel('連續事件'), self.word_layout)
        keyword_widget.addRow(QLabel('相似事件'), self.word2)

        button_layout = QHBoxLayout()
        save_btn = QPushButton("儲存")
        save_btn.clicked.connect(self.save_btn_method)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.cancel_btn_method)

        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)

        self.main_layout.addLayout(keyword_widget)
        self.main_layout.addLayout(button_layout)

        self.setLayout(self.main_layout)

    @pyqtSlot()
    def save_btn_method(self):
        def find_situation():
            events = self.word1.text()
            for key, values in enumerate(self.continuous_event.items()):
                if events in values:
                    return key
            else:
                return ""

        if self.word1.text() != '' and self.word2.toPlainText() != '':
            situation = find_situation()
            self.continuous_event[situation] = self.word2.toPlainText().split('\n')
            self.all_events.update(self.word2.toPlainText().split('\n'))
            self.model.setStringList(self.all_events)
            print(situation, self.continuous_event[situation])
            with(open(r'./data/continuous_event.json', 'w', encoding='utf-8')) as data:
                json.dump(self.continuous_event, data,indent=2, ensure_ascii=False)

            QMessageBox.information(
                self, '提醒', '已新增"{}"至資料庫'.format(self.word2.toPlainText()))

        else:
            QMessageBox.information(self, '警告', '兩欄皆須填寫內容')

    @pyqtSlot()
    def remove_btn_method(self):
        def find_situation():
            events = self.word1.text()
            for key, values in self.continuous_event.items():
                if events in values:
                    return key
            else:
                return ""

        if self.current_index != None:
            result = QMessageBox.question(self, '警告', '確定要刪除"{0}"的連續事件嗎?'.format(self.word1.text()),
                                          QMessageBox.Yes | QMessageBox.No,
                                          QMessageBox.No)
            if result == QMessageBox.Yes:
                situation = find_situation()
                self.continuous_event[situation] = []

                for i in self.synonym_events[self.current_index]:
                    self.all_events.discard(i)

                self.model.setStringList(self.all_events)
                self.word2.setText("")
                with(open(r'./data/continuous_event.json', 'w', encoding='utf-8')) as data:
                    json.dump(self.continuous_event, data,
                              indent=2, ensure_ascii=False)
            else:
                pass
        else:
            QMessageBox.information(
                self, "提醒", '資料庫中無"{}"的連續事件'.format(self.word1.text()))

    @pyqtSlot()
    def cancel_btn_method(self):
        # self.model.stringList().append(self.word1.text())
        self.word1.clear()
        self.word2.clear()
        self.pos.setCurrentIndex(0)


class ComboBox(QComboBox):
    popupAboutToBeShown = QtCore.pyqtSignal()

    def __init__(self, my_function=None):
        super().__init__()
        self.my_function = my_function

    def showPopup(self):
        self.popupAboutToBeShown.emit()
        if self.my_function is not None:
            self.my_function()
        super(ComboBox, self).showPopup()


class dig_edit_sentence(QWidget):  # 編輯情境
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # 下面五行是讀json檔裡設定的ip和port，如果要改ip(例如伺服器要架到營建署)，這樣就不用再把系統重新包成exe檔
        # with open('./config.json', 'r', encoding='utf-8') as file:
        #     config = json.load(file)
        # client = MongoClient(config['db_ip'], int(config['db_port']))
        # db = client.taroko
        # self.collection = db.origin
        with(open(r'./data/continuous_event.json', 'r', encoding='utf-8')) as data:
            self.continuous_dict = json.load(data)
        self.main_layout = QVBoxLayout()

        situation_widget = QFormLayout()
        self.select_layout = QHBoxLayout()

        self.search_text = QLineEdit()
        self.search_text.textChanged.connect(self.search_situations)

        self.tableWidget = QTableWidget()
        self.tableWidget.setRowCount(len(self.continuous_dict))
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
        self.situation = QLineEdit()
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
            try:
                data = self.situation_index_list[self.tableWidget.currentIndex().row()]
                if data != None:
                    self.situation.setText(str(data))
                    self.events.setText('\n'.join(self.continuous_dict[data]))
            except Exception:
                pass
        else:
            pass

    @pyqtSlot()
    def search_situations(self):
        self.tableWidget.clear()
        self.situation_index_list.clear()

        if not self.search_text.text() == '':
            search = []
            if self.search_text.text() in self.continuous_dict:
                search.append(self.search_text.text())
                self.tableWidget.setItem(
                    0, 0, QTableWidgetItem(self.search_text.text()))
                self.situation_index_list.append(self.search_text.text())
        else:
            search = self.continuous_dict.keys()
            self.tableWidget.setRowCount(len(search))
            for index, item in enumerate(search):
                self.tableWidget.setItem(index, 0, QTableWidgetItem(item))
                self.situation_index_list.append(item)

        # self.tableWidget.setRowCount(len(self.situation_index_list))

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
                    data = self.situation_index_list[self.tableWidget.currentIndex(
                    ).row()]
                    del self.continuous_dict[data]
                    del self.situation_index_list[self.tableWidget.currentIndex(
                    ).row()]
                    with(open(r'./data/continuous_event.json', 'w', encoding='utf-8')) as data:
                        json.dump(self.continuous_dict, data, indent=2)
                    if self.tableWidget.rowCount() == 1:
                        self.tableWidget.setItem(0, 0, QTableWidgetItem(''))

                    else:
                        self.tableWidget.removeRow(
                            self.tableWidget.currentIndex().row())

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
            events = self.events.toPlainText().split('\n')
            situation = self.situation.text()
            self.continuous_dict[situation] = events
            self.situation_index_list.append(situation)
            with(open(r'./data/continuous_event.json', 'w', encoding='utf-8')) as data:
                json.dump(self.continuous_dict, data,
                          indent=2, ensure_ascii=False)

            self.tableWidget.insertRow(self.tableWidget.rowCount())
            self.tableWidget.setItem(self.tableWidget.rowCount(
            ) - 1, 0, QTableWidgetItem(str(self.situation.text())))
            QMessageBox.information(
                self, "提醒", '已儲存"{}"'.format(self.situation.text()))

        elif len(self.situation_index_list) > 0:
            events = self.events.toPlainText().split('\n')
            situation = self.situation.text()
            self.continuous_dict[situation] = events
            with(open(r'./data/continuous_event.json', 'w', encoding='utf-8')) as data:
                json.dump(self.continuous_dict, data,
                          indent=2, ensure_ascii=False)

            self.tableWidget.setItem(self.tableWidget.currentIndex(
            ).row(), 0, QTableWidgetItem(str(self.situation.text())))
            QMessageBox.information(
                self, "提醒", '已儲存"{}"'.format(self.situation.text()))

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
        with(open(r'./data/conversation.json', 'r', encoding='utf-8')) as data:
            self.conversation_dict = json.load(data)
        self.main_layout = QVBoxLayout()

        situation_widget = QFormLayout()
        self.select_layout = QHBoxLayout()

        self.search_text = QLineEdit()
        self.search_text.textChanged.connect(self.search_situations)

        self.tableWidget = QTableWidget()
        self.tableWidget.setRowCount(len(self.conversation_dict))
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
        self.situation = QLineEdit()
        self.events = QTextEdit()

        situation_widget.addRow(QLabel('搜尋'), self.select_layout)
        situation_widget.addRow(QLabel('欲編輯情境'), self.tableWidget)
        situation_widget.addRow(QLabel('情境'), self.situation)
        situation_widget.addRow(QLabel('對話'), self.events)

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
            try:
                data = self.situation_index_list[self.tableWidget.currentIndex().row()]
                if data != None:
                    self.situation.setText(str(data))
                    self.events.setText('\n'.join(self.conversation_dict[data]))
            except Exception:
                pass
        else:
            pass

    @pyqtSlot()
    def search_situations(self):
        self.tableWidget.clear()
        self.situation_index_list.clear()

        if not self.search_text.text() == '':
            search = []
            if self.search_text.text() in self.conversation_dict:
                search.append(self.search_text.text())
                self.tableWidget.setItem(
                    0, 0, QTableWidgetItem(self.search_text.text()))
                self.situation_index_list.append(self.search_text.text())
        else:
            search = self.conversation_dict.keys()
            self.tableWidget.setRowCount(len(search))
            for index, item in enumerate(search):
                self.tableWidget.setItem(index, 0, QTableWidgetItem(item))
                self.situation_index_list.append(item)

        # self.tableWidget.setRowCount(len(self.situation_index_list))

    # finished
    @pyqtSlot()
    def state_changed(self):
        self.situation.clear()
        self.events.clear()
        if self.new_or_not.checkState():
            self.tableWidget.setDisabled(True)

        else:
            self.tableWidget.setDisabled(False)

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
                    data = self.situation_index_list[self.tableWidget.currentIndex(
                    ).row()]
                    del self.conversation_dict[data]
                    del self.situation_index_list[self.tableWidget.currentIndex(
                    ).row()]
                    with(open(r'./data/conversation.json', 'w', encoding='utf-8')) as data:
                        json.dump(self.conversation_dict, data, indent=2, ensure_ascii=False)
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
            events = self.events.toPlainText().split('\n')
            situation = self.situation.text()
            self.conversation_dict[situation] = events
            self.situation_index_list.append(situation)
            with(open(r'./data/conversation.json', 'w', encoding='utf-8')) as data:
                json.dump(self.conversation_dict, data,
                          indent=2, ensure_ascii=False)

            self.tableWidget.insertRow(self.tableWidget.rowCount())
            self.tableWidget.setItem(self.tableWidget.rowCount(
            ) - 1, 0, QTableWidgetItem(str(self.situation.text())))
            QMessageBox.information(
                self, "提醒", '已儲存"{}"'.format(self.situation.text()))

        elif len(self.situation_index_list) > 0:
            events = self.events.toPlainText().split('\n')
            situation = self.situation.text()
            self.conversation_dict[situation] = events
            with(open(r'./data/conversation.json', 'w', encoding='utf-8')) as data:
                json.dump(self.conversation_dict, data,
                          indent=2, ensure_ascii=False)

            self.tableWidget.setItem(self.tableWidget.currentIndex(
            ).row(), 0, QTableWidgetItem(str(self.situation.text())))
            QMessageBox.information(
                self, "提醒", '已儲存"{}"'.format(self.situation.text()))

        else:
            pass

    @pyqtSlot()
    def cancel_btn_method(self):
        self.search_text.clear()
        self.situation.clear()
        self.events.clear()


class dig_sentence_log(QWidget):  # 使用者對話紀錄
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        with(open(r'./data/player_conversation.json', 'r', encoding='utf-8')) as data:
            self.conversation_log = json.load(data)
            self.logs = self.conversation_log['conversation']

        self.main_layout = QVBoxLayout()

        sentence_widget = QFormLayout()
        self.select_layout = QHBoxLayout()
        self.show_all_sentences = QCheckBox('顯示所有紀錄')
        self.show_all_sentences.stateChanged.connect(self.state_changed)
        self.sentences_id = []

        self.search_text = QLineEdit()
        self.search_text.textChanged.connect(self.search_sentences)

        self.tableWidget = QTableWidget()
        self.tableWidget.setRowCount(len(self.logs))
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
        self.sentence = QTextEdit()
        self.events = QTextEdit()

        sentence_widget.addRow(QLabel('搜尋'), self.select_layout)
        sentence_widget.addRow(QLabel('對話紀錄'), self.tableWidget)
        sentence_widget.addRow(QLabel('對話語句'), self.sentence)
        sentence_widget.addRow(QLabel('連續事件'), self.events)

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

        if not self.search_text.text() == '':
            search = []
            for value in self.logs:
                if self.search_text.text() in value['sentence']:
                    search.append(value['id'])
        else:
            search = [value['id'] for value in self.conversation_log['conversation']]

        self.tableWidget.setRowCount(len(search))
        for index, item in enumerate(search):
            for index, log in enumerate(self.logs):
                if log['id'] == item:
                    self.tableWidget.setItem(index, 0, QTableWidgetItem(log['sentence']))
            self.sentence_index_list.append(item)

    @pyqtSlot()
    def show_selected_item(self):
        index = self.tableWidget.currentIndex().row()
        print(index)
        if len(self.sentence_index_list) > 0:
            _id = self.sentence_index_list[index]
            try:
                for index, log in enumerate(self.logs):
                    if log['id'] == _id:
                        self.sentence.setText(log['sentence'])
                        events = [event['event'] for event in log['events']]
                        self.events.setText(','.join(events))
            except Exception:
                pass
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
                    _id = self.sentence_index_list[current_index]
                    for index, item in enumerate(self.logs):
                        if item['id'] == _id:
                            del self.logs[index]
                            break

                    del self.sentence_index_list[self.tableWidget.currentIndex().row()]
                    if self.tableWidget.rowCount() == 1:
                        self.tableWidget.setItem(0, 0, QTableWidgetItem(''))
                    else:
                        self.tableWidget.removeRow(self.tableWidget.currentIndex().row())

                    self.conversation_log['conversation'] = self.logs
                    with(open(r'./data/player_conversation.json', 'w', encoding='utf-8')) as data:
                        json.dump(self.conversation_log, data, indent=2, ensure_ascii=False)

                else:
                    pass
            else:
                QMessageBox.information(self, '警告', '目前沒有紀錄')
        else:
            pass

    def remove_item_from_table(self):
        current_index = self.sentence_index_list[self.tableWidget.currentIndex().row()]
        _id = self.sentence_index_list[current_index]
        for index, item in enumerate(self.logs):
            if item['id'] == _id:
                del self.logs[index]
                break

        del self.sentence_index_list[self.tableWidget.currentIndex().row()]
        if self.tableWidget.rowCount() == 1:
            self.tableWidget.setItem(0, 0, QTableWidgetItem(''))
        else:
            self.tableWidget.removeRow(self.tableWidget.currentIndex().row())

        self.conversation_log['conversation'] = self.logs
        with(open(r'./data/player_conversation.json', 'w', encoding='utf-8')) as data:
            json.dump(self.conversation_log, data,indent=2, ensure_ascii=False)

    @pyqtSlot()
    def save_btn_method(self):
        if len(self.sentence_index_list) > 0:
            # data = {'uuid': self.collection_ori.find().count(), 'sentence': self.sentence.toPlainText(),
            #         'answer': self.answer.toPlainText(), 'url': '',
            #         'segmentation': '',
            #         'pos': ''}
            # self.collection_ori.insert(data)
            # QMessageBox.information(self, '提醒', '已儲存"{}"'.format(self.sentence.toPlainText()))
            self.remove_item_from_table()
            self.sentence.clear()
            self.events.clear()
        else:
            QMessageBox.information(self, '警告', '目前沒有紀錄')

    @pyqtSlot()
    def cancel_btn_method(self):
        _id = self.sentence_index_list[self.tableWidget.currentIndex().row()]
        for log in self.logs:
            if log['id'] == _id:
                self.sentence.setText(log['sentence'])
                events = [event['event'] for event in log['events']]
                self.events.setText(','.join(events))


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
        subprocess.call(['mongodump', '-d', 'taroko', '-o', 'backup/{}'.format(time.strftime(r'%Y-%m-%d'))])

        with open(r'data/backup_log.json', 'w', encoding='utf-8') as config:
            json.dump({'last_backup_date': time.strftime(r'%Y-%m-%d')}, config, indent=4, ensure_ascii=True,
                      sort_keys=True)

        QMessageBox.information(self, '提醒', '備份成功')

    def restore(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        dir_name = QFileDialog.getExistingDirectory(self)
        if dir_name:
            subprocess.call(['mongorestore', '-d', 'taroko', '--drop', dir_name])
            QMessageBox.information(self, '提醒', '還原成功')

    def excel(self):
        client = MongoClient('localhost', 27017)
        db = client.taroko
        self.collection_ori = db.origin
        sentence = []
        answer = []

        for row in self.collection_ori.find():
            sentence.append(row['sentence'])
            answer.append(row['answer'])
        df = pd.DataFrame({'Sentence': sentence, 'Answer': answer})
        # writer = pd.ExcelWriter(os.path.join(os.environ['USERPROFILE'], 'Desktop/')+time.strftime('%Y_%m_%d_%H_%M')+'.xlsx', engine='xlsxwriter')
        writer = pd.ExcelWriter(os.path.join(os.getcwd(),'Q&A_excel/') + time.strftime('%Y_%m_%d_%H_%M')+'.xlsx', engine='xlsxwriter')
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

        self.addTab(dig_edit_sentence(), '編輯情境')
        # self.addTab(dig_similarity_word(), '編輯連續事件')
        self.addTab(dig_edit_conversation(), '編輯對話')
        self.addTab(dig_sentence_log(), '對話紀錄')
        self.addTab(back_up_window(), '備份與還原')

        # Show widget
        self.show()



if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setFont(QtGui.QFont('', 12))
    main_window = QA_system_window('情境編輯系統 (Best-site Editing Tool)')
    sys.exit(app.exec_())
