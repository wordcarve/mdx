from bs4 import BeautifulSoup
import re
import json
import sys


def extract_pronunciation(soup):
    """提取音标"""
    pron = {"british": "", "american": ""}
    for phon_blk in soup.find_all("phon-blk"):
        text = phon_blk.get_text(strip=True)
        if "BrE" in str(phon_blk.parent):
            pron["british"] = text
        elif "NAmE" in str(phon_blk.parent):
            pron["american"] = text
    return pron


def extract_inflections(soup):
    """提取词形变化（root, past, prespart 等）"""
    inflections = []
    seen = set()
    for vp_g in soup.find_all("vp-g"):
        form = vp_g.get("form", "").strip()
        vp = vp_g.find("vp")
        if not vp or not form:
            continue
        word = vp.get_text(strip=True)
        key = (form, word)
        if key in seen:
            continue
        seen.add(key)
        inflections.append({"form": form, "word": word})
    return inflections


def extract_meanings(soup):
    """提取释义（带空格修复）"""
    meanings = []
    for sn_g in soup.find_all("sn-g"):
        def_block = sn_g.find("def")
        if not def_block:
            continue

        en_parts = [text.strip() for text in def_block.stripped_strings]
        def_en = " ".join(en_parts)

        chn_span = def_block.find("chn")
        def_cn = chn_span.get_text(strip=True) if chn_span else ""

        if def_en and def_cn:
            meanings.append({
                "definition": def_en,
                "translation": def_cn
            })
    return meanings


def extract_idioms(soup):
    """提取习语表达"""
    idioms = []
    for idm in soup.find_all("idm"):
        parts = [a.get_text(strip=True) for a in idm.find_all("a")]
        expr = " ".join(parts)
        chn_span = idm.find("span", {"class": "chn"})
        translation = chn_span.get_text(strip=True) if chn_span else ""
        if expr and translation:
            idioms.append({"expression": expr, "translation": translation})
    return idioms


def extract_examples(soup):
    """提取例句（英文 + 中文）"""
    examples = []
    for x_block in soup.find_all("x"):
        en_parts = [text.strip() for text in x_block.stripped_strings if not text.startswith('→')]
        en = " ".join(en_parts)

        cn_parts = [text.strip().replace('→ ', '') for text in x_block.stripped_strings if text.startswith('→')]
        cn = " ".join(cn_parts)

        if en and cn:
            examples.append({"en": en, "cn": cn})
    return examples


def extract_word_title(soup):
    """提取单词标题"""
    title = soup.find("title")
    if title:
        return title.get_text(strip=True).split(':')[0]
    return ""


def format_output(data, output_format="text"):
    """格式化输出结果（文本或 JSON）"""
    if output_format == "json":
        return json.dumps(data, ensure_ascii=False, indent=4)

    lines = []

    lines.append(f"### {data['word']}\n")

    # 音标
    if data['pronunciation']['british'] or data['pronunciation']['american']:
        lines.append("#### 音标:")
        if data['pronunciation']['british']:
            lines.append(f"- 英式: {data['pronunciation']['british']}")
        if data['pronunciation']['american']:
            lines.append(f"- 美式: {data['pronunciation']['american']}")
        lines.append("")

    # 词形变化
    if data["inflections"]:
        lines.append("#### 词形变化:")
        for inf in data["inflections"]:
            lines.append(f"- {inf['form']}: {inf['word']}")
        lines.append("")

    # 释义
    if data["meanings"]:
        lines.append("#### 释义:")
        for m in data["meanings"]:
            lines.append(f"- {m['definition']} → {m['translation']}")
        lines.append("")

    # 习语
    if data["idioms"]:
        lines.append("#### 习语 / 固定搭配:")
        for i in data["idioms"]:
            lines.append(f"- {i['expression']} → {i['translation']}")
        lines.append("")

    # 例句
    if data["examples"]:
        lines.append("#### 例句:")
        for ex in data["examples"]:
            lines.append(f"  {ex['en']}")
            lines.append(f"  → {ex['cn']}")
        lines.append("")

    return "\n".join(lines)


def parse_html_file(file_path):
    """解析 HTML 文件内容并提取数据"""
    with open(file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'lxml')

    data = {
        "word": extract_word_title(soup),
        "pronunciation": extract_pronunciation(soup),
        "inflections": extract_inflections(soup),
        "meanings": extract_meanings(soup),
        "idioms": extract_idioms(soup),
        "examples": extract_examples(soup),
    }

    return data


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_dict_entry.py <input_file> [output_format]")
        print("Example: python extract_dict_entry.py Pasted_Text_1747040830194.txt text")
        sys.exit(1)

    input_file = sys.argv[1]
    output_format = sys.argv[2] if len(sys.argv) > 2 else "text"

    data = parse_html_file(input_file)
    result = format_output(data, output_format)

    print(result)