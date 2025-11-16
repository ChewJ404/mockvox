import logging
import re

# jieba静音
import jieba

jieba.setLogLevel(logging.CRITICAL)

SPECIAL_CHARS = r"0-9〜~,.;:!?，。！？；：、·([{<（【《〈「『“‘)\]}>）】》〉」』”’\"-_——\#$%&……￥'*+<=>?@[\]^_`{|}~/ "

from split_lang import LangSplitter


def full_en(text):
    pattern = r'^(?=.*[A-Za-z])[A-Za-z0-9\s\u0020-\u007E\u2000-\u206F\u3000-\u303F\uFF00-\uFFEF]+$'
    return bool(re.match(pattern, text))


def full_cjk(text):
    # 来自wiki
    cjk_ranges = [
        (0x4E00, 0x9FFF),  # CJK Unified Ideographs
        (0x3400, 0x4DB5),  # CJK Extension A
        (0x20000, 0x2A6DD),  # CJK Extension B
        (0x2A700, 0x2B73F),  # CJK Extension C
        (0x2B740, 0x2B81F),  # CJK Extension D
        (0x2B820, 0x2CEAF),  # CJK Extension E
        (0x2CEB0, 0x2EBEF),  # CJK Extension F
        (0x30000, 0x3134A),  # CJK Extension G
        (0x31350, 0x323AF),  # CJK Extension H
        (0x2EBF0, 0x2EE5D),  # CJK Extension H
    ]

    pattern = rf"^[{SPECIAL_CHARS}]+$"

    cjk_text = ""
    for char in text:
        code_point = ord(char)
        in_cjk = any(start <= code_point <= end for start, end in cjk_ranges)
        if in_cjk or re.match(pattern, char):
            cjk_text += char
    return cjk_text

def split_jako(tag_lang, item):
    if tag_lang == "ja":
        jp_chars = r"[\u3041-\u309F\u30A0-\u30FF]"  # 仅平假名和片假名
        pattern = rf"{jp_chars}+"
    else:
        ko_chars = r"[\uAC00-\uD7AF\u1100-\u11FF\u3130-\u318F]"
        pattern = rf"{ko_chars}+"

    text = item["text"]
    lang_list = []
    last_end = 0
    has_valid_match = False

    for match in re.finditer(pattern, text):
        start, end = match.span()
        matched_text = match.group()

        # 添加有效性校验
        if not is_valid_foreign_fragment(matched_text, tag_lang):
            continue

        if start > last_end:
            lang_list.append({"lang": item["lang"], "text": text[last_end:start]})
        
        lang_list.append({"lang": tag_lang, "text": matched_text})
        last_end = end
        has_valid_match = True

    if last_end < len(text):
        lang_list.append({"lang": item["lang"], "text": text[last_end:]})
    
    return lang_list if has_valid_match else [item]

def is_valid_foreign_fragment(text, tag_lang):
    """
    校验匹配到的片段是否是一个有效的、有意义的日语/韩语片段
    用于防止过度匹配和噪音干扰
    """
    # 0. 长度校验：排除单个字符（除非是特别有意义的独立字符）
    if len(text) <= 1:
        # 可以根据需要设置一个白名单，例如日文的“の”、韩文的“는”等常见独立词
        if tag_lang == "ja" and text in ["の", "に", "は", "が"]:
            return True
        elif tag_lang == "ko" and text in ["는", "을", "를", "이", "가"]:
            return True
        else:
            return False  # 单个字符通常不构成有意义的片段

    # 1. 计算目标语言字符的比例，确保片段主要由目标语言字符构成，而不是混杂大量其他字符
    if tag_lang == "ja":
        # 统计平假名、片假名等日文特有字符
        jp_char_count = sum(1 for c in text if '\u3040' <= c <= '\u309F' or '\u30A0' <= c <= '\u30FF')
        if jp_char_count / len(text) < 0.6:  # 设定阈值需要60%以上是日文字符
            return False
    else:  # ko
        ko_char_count = sum(1 for c in text if '\uAC00' <= c <= '\uD7AF')
        if ko_char_count / len(text) < 0.7:  # 韩文音节块通常成片出现，阈值可设高些
            return False

    return True

# 返回lang_list前添加校正
def correct_common_errors(lang_list):
    corrected = []
    for i, item in enumerate(lang_list):
        # 规则1：短中文片段不应标记为日语
        if (item['lang'] == 'ja' and 
            len(item['text']) <= 2 and 
            any('\u4e00' <= c <= '\u9fff' for c in item['text'])):
            # 检查上下文：如果前后都是中文，则校正
            if (i > 0 and lang_list[i-1]['lang'] == 'zh') or \
               (i < len(lang_list)-1 and lang_list[i+1]['lang'] == 'zh'):
                item['lang'] = 'zh'
        
        # 规则2：纯标点片段继承前后语言
        if all(c in SPECIAL_CHARS for c in item['text'].strip()):
            if corrected and i < len(lang_list)-1:
                item['lang'] = corrected[-1]['lang']  # 继承前一个语言
        
        corrected.append(item)
    return corrected

def merge_lang(lang_list, item):
    if lang_list and item["lang"] == lang_list[-1]["lang"]:
        lang_list[-1]["text"] += item["text"]
    else:
        lang_list.append(item)
    return lang_list


class LangSegmenter:
    # 默认过滤器, 基于gsv目前四种语言
    DEFAULT_LANG_MAP = {
        "zh": "zh",
        "yue": "zh",  # 粤语
        "wuu": "zh",  # 吴语
        "zh-cn": "zh",
        "zh-tw": "x",  # 繁体设置为x
        "ko": "ko",
        "ja": "ja",
        "en": "en",
    }

    @staticmethod
    def getTexts(text,default_lang = ""):
        if not text or text.strip() == "":
            return []
        
        lang_splitter = LangSplitter(lang_map=LangSegmenter.DEFAULT_LANG_MAP)
        lang_splitter.merge_across_digit = False
        substr = lang_splitter.split_by_lang(text=text)

        lang_list: list[dict] = []
        have_num = False
        for _, item in enumerate(substr):
            dict_item = {"lang": item.lang, "text": item.text}

            # 处理短英文被识别为其他语言的问题
            if dict_item['lang'] == 'digit':
                if default_lang != "":
                    dict_item['lang'] = default_lang
                else:
                    have_num = True
                lang_list = merge_lang(lang_list,dict_item)
                continue

            if full_en(dict_item['text']):  
                dict_item['lang'] = 'en'
                lang_list = merge_lang(lang_list,dict_item)
                continue
            if default_lang != "":
                dict_item['lang'] = default_lang
                lang_list = merge_lang(lang_list,dict_item)
                continue
            else:
                # 处理非日语夹日文的问题(不包含CJK)
                ja_list: list[dict] = []
                if dict_item['lang'] != 'ja':
                    ja_list = split_jako('ja',dict_item)

                if not ja_list:
                    ja_list.append(dict_item)

                # 处理非韩语夹韩语的问题(不包含CJK)
                ko_list: list[dict] = []
                temp_list: list[dict] = []
                for _, ko_item in enumerate(ja_list):
                    if ko_item["lang"] != 'ko':
                        ko_list = split_jako('ko',ko_item)

                    if ko_list:
                        temp_list.extend(ko_list)
                    else:
                        temp_list.append(ko_item)

                # 未存在非日韩文夹日韩文
                if len(temp_list) == 1:
                    # 未知语言检查是否为CJK
                    if dict_item['lang'] == 'x':
                        cjk_text = full_cjk(dict_item['text'])
                        if cjk_text:
                            dict_item = {'lang':'zh','text':cjk_text}
                            lang_list = merge_lang(lang_list,dict_item)
                        else:
                            lang_list = merge_lang(lang_list,dict_item)
                        continue
                    else:
                        lang_list = merge_lang(lang_list,dict_item)
                        continue

                # 存在非日韩文夹日韩文
                for _, temp_item in enumerate(temp_list):
                    # 未知语言检查是否为CJK
                    if temp_item['lang'] == 'x':
                        cjk_text = full_cjk(temp_item['text'])
                        if cjk_text:
                            lang_list = merge_lang(lang_list,{'lang':'zh','text':cjk_text})
                        else:
                            lang_list = merge_lang(lang_list,temp_item)
                    else:
                        lang_list = merge_lang(lang_list,temp_item)

        # 有数字
        if have_num:
            temp_list = lang_list
            lang_list = []
            for i, temp_item in enumerate(temp_list):
                if temp_item['lang'] == 'digit':
                    if default_lang:
                        temp_item['lang'] = default_lang
                    elif lang_list and i == len(temp_list) - 1:
                        temp_item['lang'] = lang_list[-1]['lang']
                    elif not lang_list and i < len(temp_list) - 1:
                        temp_item['lang'] = temp_list[i+1]['lang']
                    elif lang_list and i < len(temp_list) - 1:
                        if lang_list[-1]['lang'] == temp_list[i + 1]['lang']:
                            temp_item['lang'] = lang_list[-1]['lang']
                        elif lang_list[-1]['text'][-1] in [",",".","!","?","，","。","！","？"]:
                            temp_item['lang'] = temp_list[i + 1]['lang']
                        elif temp_list[i + 1]['text'][0] in [",",".","!","?","，","。","！","？"]:
                            temp_item['lang'] = lang_list[-1]['lang']
                        elif temp_item['text'][-1] in ["。","."]:
                            temp_item['lang'] = lang_list[-1]['lang']
                        elif len(lang_list[-1]['text']) >= len(temp_list[i + 1]['text']):
                            temp_item['lang'] = lang_list[-1]['lang']
                        else:
                            temp_item['lang'] = temp_list[i + 1]['lang']
                    else:
                        temp_item['lang'] = 'zh'

                lang_list = merge_lang(lang_list,temp_item)


        # 筛X
        temp_list = lang_list
        lang_list = []
        for _, temp_item in enumerate(temp_list):
            if temp_item['lang'] == 'x':
                if lang_list:
                    temp_item['lang'] = lang_list[-1]['lang']
                elif len(temp_list) > 1:
                    temp_item['lang'] = temp_list[1]['lang']
                else:
                    temp_item['lang'] = 'zh'

            lang_list = merge_lang(lang_list,temp_item)

        lang_list = correct_common_errors(lang_list)
        return lang_list
