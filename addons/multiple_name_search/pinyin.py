#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
    Author:cleverdeng
    E-mail:clverdeng@gmail.com
"""

__version__ = '0.9'
__all__ = ["PinYin"]

import os.path


class PinYin(object):
    def __init__(self, dict_file=None):
        self.word_dict = {}
        self.dict_file = dict_file if dict_file is not None else os.path.split(os.path.realpath(__file__))[0] + os.sep + 'word.data'  # 文件路径


    def load_word(self):
        if not os.path.exists(self.dict_file):
            raise IOError("Not found %s" % self.dict_file)

        with open(self.dict_file, 'r') as f_obj:
            for f_line in f_obj.readlines():
                try:
                    line = f_line.split('    ')
                    self.word_dict[line[0]] = line[1]
                except:
                    line = f_line.split('   ')
                    self.word_dict[line[0]] = line[1]


    def hanzi2pinyin(self, string=""):
        result = []
        if not isinstance(string, unicode):
            string = string.decode("utf-8")
        for char in string:
            key = '%X' % ord(char)
            result.append(self.word_dict.get(key, char).split()[0][:-1].lower())
        return result
    
    def hanzi2pinyin_split(self, string="", split=""):
        result = self.hanzi2pinyin(string=string)
        # if split == "":
        #    return result
        # else:
        return split.join(result)
    
    # 字符串里有汉字也有其他字符
    def str2pinyin(self, string=""):
        result = []
        if not isinstance(string, unicode):
            string = string.decode("utf-8")
        for char in string:
            cIndex = ord(char)  # 字符的位置
            result.append(self.word_dict.get('%X' % cIndex, char).split()[0][:-1].lower() if cIndex >= 0x4e00 and cIndex <= 0x9fff else unichr(cIndex))
        return result

if __name__ == "__main__":
    test = PinYin()
    test.load_word()
    string = "钓鱼岛是中国的"
    print "in: %s" % string
    print "out: %s" % str(test.hanzi2pinyin(string=string))
    print "out: %s" % test.hanzi2pinyin_split(string=string, split="-")
