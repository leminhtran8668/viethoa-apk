#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import glob
import argparse
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from deep_translator import GoogleTranslator

# ==========================================
# 1. TỪ ĐIỂN ƯU TIÊN (CHUYÊN NGÀNH Ô TÔ & ANDROID)
# ==========================================
CUSTOM_GLOSSARY = {
    "确定": "Xác nhận",
    "取消": "Hủy",
    "设置": "Cài đặt",
    "系统设置": "Cài đặt hệ thống",
    "蓝牙": "Bluetooth",
    "行车记录仪": "Cam hành trình",
    "摄像头": "Camera",
    "车门": "Cửa xe",
    "左前门": "Cửa trước trái",
    "右前门": "Cửa trước phải",
    "左后门": "Cửa sau trái",
    "右后门": "Cửa sau phải",
    "后备箱": "Cốp xe",
    "引擎盖": "Nắp capo",
    "音量": "Âm lượng",
    "静音": "Tắt tiếng",
    "密码": "Mật khẩu",
    "提示": "Thông báo",
    "警告": "Cảnh báo",
    "成功": "Thành công",
    "失败": "Thất bại",
    "正在加载": "Đang tải...",
    "请稍候": "Vui lòng chờ...",
    "退出": "Thoát",
    "保存": "Lưu",
    "开启": "Bật",
    "关闭": "Tắt",
    "已开启": "Đã bật",
    "已关闭": "Đã tắt",
    "主页": "Trang chủ",
    "返回": "Quay lại",
    "刷新": "Làm mới",
    "删除": "Xóa",
    "清空": "Xóa sạch",
    "版本": "Phiên bản",
    "权限": "Quyền truy cập",
}

TRANSLATION_CACHE = dict(CUSTOM_GLOSSARY)

CJK_REGEX = re.compile(r'[\u4e00-\u9fff]')
PLACEHOLDER_REGEX = re.compile(r'(%(\d+\$)?[-#+ 0,(]*\d*\.?\d*[sdfoxegcbh]|\{\d+\}|\\n|\\t)')
FORMAT_SPECIFIER_REGEX = re.compile(r'%(\d+\$)?[-#+ 0,(]*\d*\.?\d*[sdfoxegcbh]')

def has_chinese(text):
    return bool(CJK_REGEX.search(text))

def extract_format_specifiers(text):
    return [m.group(0) for m in FORMAT_SPECIFIER_REGEX.finditer(text)]

def validate_format_specifiers(original, translated):
    orig_specs = sorted(extract_format_specifiers(original))
    trans_specs = sorted(extract_format_specifiers(translated))
    return orig_specs == trans_specs

def protect_placeholders(text):
    placeholders = []
    def replacer(match):
        placeholders.append(match.group(0))
        return f"__PH{len(placeholders)-1}__"
    return PLACEHOLDER_REGEX.sub(replacer, text), placeholders

def restore_placeholders(text, placeholders):
    for i, ph in enumerate(placeholders):
        text = re.sub(rf'__\s*PH\s*{i}\s*__', lambda _: ph, text, flags=re.IGNORECASE)
    return text

def should_skip_string(text):
    if not text or not text.strip():
        return True
    t = text.strip()
    if t.startswith(('http://', 'https://', 'file://', 'content://', '@string/', '@drawable/', '@color/', '@style/', 'Lcom/', 'Landroid/')):
        return True
    if re.match(r'^[a-zA-Z0-9_.\-/:]+$', t):
        return True
    return False

def translate_single(text, force_cjk_only=False):
    if should_skip_string(text):
        return text
    if force_cjk_only and not has_chinese(text):
        return text

    clean_text = text.strip()
    if clean_text in TRANSLATION_CACHE:
        cached = TRANSLATION_CACHE[clean_text]
        if validate_format_specifiers(clean_text, cached):
            return text.replace(clean_text, cached)
        return text

    try:
        translator = GoogleTranslator(source='auto', target='vi')
        protected, phs = protect_placeholders(clean_text)
        translated = translator.translate(protected)
        if translated:
            restored = restore_placeholders(translated, phs)
            if validate_format_specifiers(clean_text, restored):
                TRANSLATION_CACHE[clean_text] = restored
                return restored
            else:
                TRANSLATION_CACHE[clean_text] = clean_text
                return text
    except Exception as e:
        print(f"Lỗi dịch '{clean_text}': {e}")
    return text

def batch_warm_cache(unique_strings):
    to_translate = [s for s in unique_strings if s not in TRANSLATION_CACHE and not should_skip_string(s)]
    if not to_translate:
        return
    print(f"Đang dịch đa luồng {len(to_translate)} chuỗi mới...")
    with ThreadPoolExecutor(max_workers=5) as executor:
        list(executor.map(translate_single, to_translate))

def fix_manifest_anti_crash(decompiled_dir, strip_shared_uid=False):
    manifest_path = os.path.join(decompiled_dir, "AndroidManifest.xml")
    if not os.path.exists(manifest_path):
        return

    print("Đang tối ưu hóa AndroidManifest.xml...")
    with open(manifest_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    content = content.replace('android:extractNativeLibs="false"', 'android:extractNativeLibs="true"')

    split_attrs = [
        r'\s*android:isSplitRequired="true"',
        r'\s*android:requiredSplitTypes="[^"]*"',
        r'\s*android:splitTypes="[^"]*"',
    ]
    for pat in split_attrs:
        content = re.sub(pat, '', content)

    bad_meta_Regex = re.compile(
        r'<meta-data[^>]+android:name="(?:com\.android\.vending\.splits|com\.android\.vending\.derived\.apk\.id|com\.android\.stamp\.source|com\.android\.stamp\.type)"[^>]*/?>',
        re.IGNORECASE
    )
    content = bad_meta_Regex.sub('', content)

    if strip_shared_uid:
        content = re.sub(r'\s*android:sharedUserId="[^"]*"', '', content)
        content = re.sub(r'\s*android:sharedUserLabel="[^"]*"', '', content)

    with open(manifest_path, 'w', encoding='utf-8') as f:
        f.write(content)

def fix_apktool_yml(decompiled_dir):
    yml_path = os.path.join(decompiled_dir, "apktool.yml")
    if not os.path.exists(yml_path):
        return
    with open(yml_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    if "doNotCompress:" in content and "- so" not in content:
        content = content.replace("doNotCompress:", "doNotCompress:\n- so\n- arsc")
        with open(yml_path, 'w', encoding='utf-8') as f:
            f.write(content)

def sanitize_xml_text(text):
    text = text.replace("\\'", "'").replace("'", "\\'")
    text = text.replace('\\"', '"').replace('"', '\\"')
    return text

def process_values_xml(input_path, output_path, only_chinese=False):
    if not os.path.exists(input_path):
        return
    try:
        tree = ET.parse(input_path)
        root = tree.getroot()
    except Exception:
        return

    elements_to_translate = []
    for elem in root.findall('string'):
        if elem.attrib.get('translatable') != 'false' and elem.text:
            name_attr = elem.attrib.get('name', '').lower()
            if any(skip_k in name_attr for skip_k in ['_key', 'pref_', 'config_', 'url_', 'path_', 'class_']):
                if not has_chinese(elem.text):
                    continue
            if not only_chinese or has_chinese(elem.text):
                elements_to_translate.append(elem)

    for parent_tag in ['string-array', 'plurals']:
        for parent in root.findall(parent_tag):
            name_attr = parent.attrib.get('name', '').lower()
            if any(skip_k in name_attr for skip_k in ['_values', 'entryvalues', '_keys']):
                continue
            if parent.attrib.get('translatable') != 'false':
                for item in parent.findall('item'):
                    if item.text and (not only_chinese or has_chinese(item.text)):
                        elements_to_translate.append(item)

    unique_texts = {el.text.strip() for el in elements_to_translate if el.text}
    batch_warm_cache(unique_texts)

    for el in elements_to_translate:
        translated = translate_single(el.text, force_cjk_only=only_chinese)
        el.text = sanitize_xml_text(translated)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    tree.write(output_path, encoding='utf-8', xml_declaration=True)

LAYOUT_ATTR_REGEX = re.compile(
    r'(android:(?:text|hint|title|summary|dialogTitle|positiveButtonText|negativeButtonText)=")([^"@][^"]*?)(")'
)

def process_layout_files(base_res_dir):
    xml_files = glob.glob(os.path.join(base_res_dir, "layout*/*.xml")) + \
                glob.glob(os.path.join(base_res_dir, "xml*/*.xml"))
    
    unique_strings = set()
    file_matches = []

    for fpath in xml_files:
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        matches = LAYOUT_ATTR_REGEX.findall(content)
        cjk_matches = [m[1] for m in matches if has_chinese(m[1])]
        if cjk_matches:
            unique_strings.update(cjk_matches)
            file_matches.append(fpath)

    batch_warm_cache(unique_strings)

    for fpath in file_matches:
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        def replacer(match):
            prefix, val, suffix = match.groups()
            if has_chinese(val):
                trans = translate_single(val, force_cjk_only=True)
                trans = trans.replace('"', '&quot;').replace("'", "\\'")
                trans = trans.replace('<', '&lt;').replace('>', '&gt;')
                return f"{prefix}{trans}{suffix}"
            return match.group(0)

        new_content = LAYOUT_ATTR_REGEX.sub(replacer, content)
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(new_content)

SMALI_CONST_STRING_REGEX = re.compile(r'^(\s*const-string(?:/jumbo)?\s+[vp]\d+,\s*")(.+)("\s*)$')
UNICODE_ESCAPE_REGEX = re.compile(r'\\u([0-9a-fA-F]{4})')

DANGEROUS_SMALI_CALLS = (
    'SharedPreferences', 'JSONObject', 'JSONArray', 'Intent;-><init>',
    'Intent;->putExtra', 'Intent;->get', 'Bundle;->put', 'Bundle;->get',
    'Class;->forName', 'Class;->getDeclared', 'Enum;->valueOf',
    'SQLiteDatabase', 'MessageDigest', 'Cipher', 'System;->loadLibrary',
)

def decode_smali_unicode(s):
    return UNICODE_ESCAPE_REGEX.sub(lambda m: chr(int(m.group(1), 16)), s)

def escape_for_smali(s):
    s = s.replace('\\"', '"').replace('"', '\\"')
    s = s.replace('\n', '\\n').replace('\r', '')
    return s

def is_safe_smali_ui_string(decoded_str):
    if not has_chinese(decoded_str):
        return False
    if len(decoded_str) > 100:
        return False
    if any(k in decoded_str for k in ['SELECT ', 'INSERT ', 'UPDATE ', 'DELETE ', 'http://', 'https://', '{"', '":', 'Exception', '/system/', '/data/']):
        return False
    return True

def process_smali_files(decompiled_dir):
    smali_files = glob.glob(os.path.join(decompiled_dir, "smali*/**/*.smali"), recursive=True)
    unique_cjk_strings = set()
    target_smali_files = []

    for sf in smali_files:
        norm_path = sf.replace('\\', '/')
        if any(skip in norm_path for skip in ['/androidx/', '/android/support/', '/kotlin/', '/kotlinx/', '/com/google/', '/okhttp3/', '/retrofit2/', '/com/gson/', '/org/json/']):
            continue

        with open(sf, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        file_has_cjk = False
        for idx, line in enumerate(lines):
            m = SMALI_CONST_STRING_REGEX.match(line)
            if m:
                raw_str = m.group(2)
                decoded = decode_smali_unicode(raw_str)
                if is_safe_smali_ui_string(decoded):
                    next_context = "".join(lines[idx+1:idx+5])
                    if any(danger in next_context for danger in DANGEROUS_SMALI_CALLS):
                        continue
                    unique_cjk_strings.add(decoded)
                    file_has_cjk = True

        if file_has_cjk:
            target_smali_files.append(sf)

    batch_warm_cache(unique_cjk_strings)

    for sf in target_smali_files:
        with open(sf, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        new_lines = []
        for idx, line in enumerate(lines):
            m = SMALI_CONST_STRING_REGEX.match(line)
            if m:
                prefix, raw_str, suffix = m.groups()
                decoded = decode_smali_unicode(raw_str)
                if is_safe_smali_ui_string(decoded):
                    next_context = "".join(lines[idx+1:idx+5])
                    if not any(danger in next_context for danger in DANGEROUS_SMALI_CALLS):
                        translated = translate_single(decoded, force_cjk_only=True)
                        safe_trans = escape_for_smali(translated)
                        line = f"{prefix}{safe_trans}{suffix}\n"
            new_lines.append(line)

        with open(sf, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="decompiled_apk")
    parser.add_argument("--strip-shared-uid", action="store_true")
    parser.add_argument("--skip-smali", action="store_true")
    args = parser.parse_args()

    decompiled_dir = args.dir
    base_res = os.path.join(decompiled_dir, "res")

    fix_manifest_anti_crash(decompiled_dir, strip_shared_uid=args.strip_shared_uid)
    fix_apktool_yml(decompiled_dir)

    for xml_name in ["strings.xml", "arrays.xml", "plurals.xml"]:
        default_file = os.path.join(base_res, f"values/{xml_name}")
        vi_file = os.path.join(base_res, f"values-vi/{xml_name}")
        
        if os.path.exists(default_file):
            process_values_xml(default_file, vi_file, only_chinese=False)
            process_values_xml(default_file, default_file, only_chinese=False)

        for zh_dir in ["values-zh", "values-zh-rCN", "values-zh-rTW", "values-zh-rHK"]:
            zh_file = os.path.join(base_res, f"{zh_dir}/{xml_name}")
            if os.path.exists(zh_file):
                process_values_xml(zh_file, zh_file, only_chinese=False)
                if not os.path.exists(vi_file):
                    process_values_xml(zh_file, vi_file, only_chinese=False)

    if os.path.exists(base_res):
        process_layout_files(base_res)

    if not args.skip_smali:
        process_smali_files(decompiled_dir)

    print("=== HOÀN TẤT VIỆT HÓA SÂU & BẢO VỆ CHỐNG VĂNG APK ===")
