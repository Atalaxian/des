import binascii
import operator
import os
import sys
from functools import reduce
from textwrap import wrap

from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog

from constants import START_PERMUTATION, FINAL_PERMUTATION, SUB_BOX, PERMUTATION, \
    EXPANSION, PERMUTED_CHOICE_1, PERMUTED_CHOICE_2, ROTATES
from error_window import Ui_widget
from main_window import Ui_Form


class MyException(Exception):
    text = None

    def __init__(self, text) -> None:
        super().__init__()
        self.text = text


class ErrorWindow(QWidget, Ui_widget):
    def __init__(self, text) -> None:
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle('Ошибка')
        self.error_label.setText(text)


class DES:
    key = None
    text = None

    def __init__(self, text, key=None) -> None:
        self.text = text
        if key is None:
            self.key = binascii.hexlify(os.urandom(8)).decode('ascii')
        else:
            if len(self.to_bin(key)) != 64:
                raise MyException('Ключ должен состоять из 64 бит.')
            else:
                self.key = key

    def get_key(self) -> str:
        return self.key

    def code_text(self) -> str:
        encrypted_bits = list()
        for i in self.slice_text(self.text):
            bin_mess, bin_key = self.to_bin(i), self.to_bin(self.key)

            permuted_key, permuted_block = self.permute(
                bin_key, PERMUTED_CHOICE_1), self.permute(bin_mess, START_PERMUTATION)

            key_list = self.key_gen(
                permuted_key[: len(permuted_key) // 2], permuted_key[len(permuted_key) // 2:])

            encrypted_bits.append(''.join([hex(int(i, 2))[2:].zfill(
                2).upper() for i in self.des(permuted_block, key_list)]))

        return ''.join(encrypted_bits)

    def decode_text(self) -> str:
        temp_li = []
        for i in wrap(self.text, 16):
            bin_mess, bin_key = self.to_bin(i), self.to_bin(self.key)

            permuted_key, permuted_block = self.permute(
                bin_key, PERMUTED_CHOICE_1), self.permute(bin_mess, START_PERMUTATION)

            key_list = self.key_gen(
                permuted_key[: len(permuted_key) // 2], permuted_key[len(permuted_key) // 2:])

            temp_li.append(''.join([hex(int(i, 2))[2:].zfill(2).upper()
                                    for i in self.des(permuted_block, reversed(key_list))]))

        return ''.join(self.concatenate(
            [[chr(int(j, 16)) for j in wrap(i, 2) if int(j, 16) != 0] for i in temp_li]))

    @staticmethod
    def slice_text(string) -> list:
        return [i.zfill(16) for i in wrap(''.join([hex(ord(i))[2:] for i in string]), 16)]

    @staticmethod
    def to_bin(s) -> str:
        return ''.join([bin(int(i, 16))[2:].zfill(4) for i in s])

    @staticmethod
    def permute(block, permutation_array) -> str:
        return ''.join([block[i] for i in permutation_array])

    @staticmethod
    def xor(arg_1, arg_2) -> str:
        return ''.join([str(int(i) ^ int(j)) for i, j in zip(arg_1, arg_2)])

    @staticmethod
    def rotate_left(block, i):
        return bin(int(block, 2) << i & 0x0fffffff | int(block, 2) >> 28 - i)[2:].zfill(28)

    @staticmethod
    def concatenate(args):
        return reduce(operator.iadd, args, [])

    def key_gen(self, block_1, block_2):
        li = []
        for i in ROTATES:
            block_1 = self.rotate_left(block_1, i)
            block_2 = self.rotate_left(block_2, i)
            li.append(self.permute(block_1 + block_2, PERMUTED_CHOICE_2))

        return li

    def f(self, block, key) -> str:
        final = []

        for j, i in enumerate(wrap(self.xor(self.permute(block, EXPANSION), key), 6)):
            temp_box = [
                SUB_BOX[j][0:16],
                SUB_BOX[j][16:32],
                SUB_BOX[j][32:48],
                SUB_BOX[j][48:64]
            ]
            final.append(bin(temp_box[int(i[0] + i[-1], 2)]
                             [int(i[1:-1], 2)])[2:].zfill(4))

        return self.permute(''.join(final), PERMUTATION)

    def des(self, block, key_array) -> str:

        left, right = block[0: len(block) // 2], block[len(block) // 2:]
        for j, i in zip(range(1, 17), key_array):
            right, left = self.xor(self.f(right, i), left), right
        return wrap(self.permute(right + left, FINAL_PERMUTATION), 8)


class MainWindow(QWidget, Ui_Form):
    error_window = None

    def __init__(self) -> None:
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle('Шифр DES')
        self.code_text.clicked.connect(self.code_text_des)
        self.save_code_text.clicked.connect(self.save_code_file)
        self.load_text_for_code.clicked.connect(self.load_code_file)
        self.load_text_for_decode.clicked.connect(self.load_decode_file)
        self.save_decode_text.clicked.connect(self.save_decode_file)
        self.decode_text.clicked.connect(self.decode_text_des)

    @QtCore.pyqtSlot()
    def code_text_des(self) -> None:
        text = self.code_start.toPlainText()
        text = text.replace('\n', 'MYNULL')
        if len(text) == 0:
            self.error_window = ErrorWindow('Текст для кодирования отсутствует.')
            self.error_window.show()
            return
        key = None
        if self.key_set.isChecked():
            key = self.code_key.text()
            if len(key) == 0:
                self.error_window = ErrorWindow('Ключ не задан.')
                self.error_window.show()
                return
        try:
            coder = DES(text, key)
        except MyException as e:
            self.error_window = ErrorWindow(e.text)
            self.error_window.show()
            return
        if key is None:
            self.code_key.setText(coder.get_key())
        code_text = coder.code_text()
        self.code_end.setText(code_text)

    @QtCore.pyqtSlot()
    def decode_text_des(self) -> None:
        text = self.decode_start.toPlainText()
        if len(text) == 0:
            self.error_window = ErrorWindow('Текст для декодирования отсутствует.')
            self.error_window.show()
            return
        key = self.decode_key.text()
        if len(key) == 0:
            self.error_window = ErrorWindow('Ключ не задан.')
            self.error_window.show()
            return
        try:
            decoder = DES(text, key)
        except MyException as e:
            self.error_window = ErrorWindow(e.text)
            self.error_window.show()
            return
        decode_text = decoder.decode_text()
        decode_text = decode_text.replace('MYNULL', '\n')
        self.decode_end.setText(decode_text)

    @QtCore.pyqtSlot()
    def load_code_file(self) -> None:
        filegialog = QFileDialog.getOpenFileUrl(self, 'Загрузка',
                                                filter=str("Текстовый файл (*.txt)"))
        if filegialog[0]:
            file_path = filegialog[0].toLocalFile()
            if file_path == '':
                return
            file = open(file_path, 'r', encoding='UTF-8')
            text = file.read()
            self.code_start.setText(text)

    @QtCore.pyqtSlot()
    def load_decode_file(self) -> None:
        filegialog = QFileDialog.getOpenFileUrl(self, 'Загрузка',
                                                filter=str("Текстовый файл (*.txt)"))
        if filegialog[0]:
            file_path = filegialog[0].toLocalFile()
            if file_path == '':
                return
            file = open(file_path, 'r', encoding='UTF-8')
            text = file.read()
            self.decode_start.setText(text)

    @QtCore.pyqtSlot()
    def save_code_file(self) -> None:
        text = self.code_end.toPlainText()
        if len(text) == 0:
            self.error_window = ErrorWindow('Нет закодированных данных')
            self.error_window.show()
            return
        filegialog = QFileDialog.getSaveFileUrl(self, 'Сохранение',
                                                filter=str("Текстовый файл (*.txt)"))
        if filegialog[0]:
            file_path = filegialog[0].toLocalFile()
            if file_path == '':
                return
            file = open(file_path, 'w', encoding='UTF-8')
            file.write(text)

    @QtCore.pyqtSlot()
    def save_decode_file(self) -> None:
        text = self.decode_end.toPlainText()
        if len(text) == 0:
            self.error_window = ErrorWindow('Нет декодированных данных')
            self.error_window.show()
            return
        filegialog = QFileDialog.getSaveFileUrl(self, 'Сохранение',
                                                filter=str("Текстовый файл (*.txt)"))
        if filegialog[0]:
            file_path = filegialog[0].toLocalFile()
            if file_path == '':
                return
            file = open(file_path, 'w', encoding='UTF-8')
            file.write(text)


if __name__ == '__main__':
    qapp = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(qapp.exec())
