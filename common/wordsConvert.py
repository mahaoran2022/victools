# -*- coding: UTF-8 -*-
import pypinyin
import re


# 不带声调的(style=pypinyin.NORMAL)
def pinyin(word):
    s = ''
    for i in pypinyin.pinyin(word, style=pypinyin.NORMAL):
        s += ''.join(i)
    return s


# 带声调的(默认)
def yinjie(word):
    s = ''
    # heteronym=True开启多音字
    for i in pypinyin.pinyin(word, heteronym=True):
        s = s + ''.join(i) + " "
    return s


# 去掉空格
def trim(word):
    newword = ''
    for ch in word:          #遍历每一个字符串
        if ch!=' ':
            newword = newword + ch
    return newword


# 去掉括号
def without_parentheses(word):
    word = word.split(u'（')[0]
    word = word.split('(')[0]
    return word


# 去掉空格，并转拼音
def pinyin_without_parentheses(word):
    word = trim(word)
    word = without_parentheses(word)
    word = re.sub(u"([^\u4e00-\u9fa5\u0030-\u0039\u0041-\u005a\u0061-\u007a])", "", word)   ##去掉特殊字符
    word = pinyin(word)
    return word


if __name__ == "__main__":
    print(pinyin(u"忠厚传家久"))
    print(yinjie(u"诗书继世长"))
    print pinyin_without_parentheses(u"乌斯季-乌里马     ")
