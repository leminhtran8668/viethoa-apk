#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deep Viet Hoa APK + Anti-Crash
Dùng Google GTX (translate.googleapis.com) — ổn định hơn deep-translator trên CI.
Offline glossary ưu tiên; circuit-breaker khi bị rate-limit.
"""

import os, re, sys, glob, time, argparse, json, urllib.parse, urllib.request
import xml.etree.ElementTree as ET

MAX_TRANSLATE_SECONDS = 25 * 60
MAX_STRINGS = 3000
SLEEP_OK = 0.25
SLEEP_ERR = 2.0
BATCH_PRINT_EVERY = 40
MAX_CONSECUTIVE_FAILS = 8

CUSTOM_GLOSSARY = {
    "确定": "Xác nhận", "取消": "Hủy", "设置": "Cài đặt", "系统设置": "Cài đặt hệ thống",
    "蓝牙": "Bluetooth", "行车记录仪": "Cam hành trình", "摄像头": "Camera",
    "车门": "Cửa xe", "左前门": "Cửa trước trái", "右前门": "Cửa trước phải",
    "左后门": "Cửa sau trái", "右后门": "Cửa sau phải", "后备箱": "Cốp xe",
    "引擎盖": "Nắp capo", "音量": "Âm lượng", "静音": "Tắt tiếng", "密码": "Mật khẩu",
    "提示": "Thông báo", "警告": "Cảnh báo", "成功": "Thành công", "失败": "Thất bại",
    "正在加载": "Đang tải...", "请稍候": "Vui lòng chờ...", "退出": "Thoát", "保存": "Lưu",
    "开启": "Bật", "关闭": "Tắt", "已开启": "Đã bật", "已关闭": "Đã tắt",
    "主页": "Trang chủ", "返回": "Quay lại", "刷新": "Làm mới", "删除": "Xóa",
    "清空": "Xóa sạch", "版本": "Phiên bản", "权限": "Quyền truy cập",
    "开始": "Bắt đầu", "结束": "Kết thúc", "下一步": "Tiếp theo", "上一步": "Quay lại",
    "完成": "Hoàn tất", "搜索": "Tìm kiếm", "帮助": "Trợ giúp", "关于": "Giới thiệu",
    "语言": "Ngôn ngữ", "中文": "Tiếng Trung", "英文": "Tiếng Anh",
    "导航": "Điều hướng", "地图": "Bản đồ", "音乐": "Nhạc", "视频": "Video",
    "电话": "Điện thoại", "信息": "Tin nhắn", "应用": "Ứng dụng", "文件": "Tệp",
    "下载": "Tải xuống", "上传": "Tải lên", "连接": "Kết nối", "断开": "Ngắt",
    "温度": "Nhiệt độ", "空调": "Điều hòa", "座椅": "Ghế", "方向盘": "Vô lăng",
    "胎压": "Áp suất lốp", "续航": "Quãng đường", "电量": "Pin", "充电": "Sạc",
    "登录": "Đăng nhập", "注册": "Đăng ký", "用户": "Người dùng", "账户": "Tài khoản",
    "网络": "Mạng", "无线": "Không dây", "热点": "Điểm phát sóng", "亮度": "Độ sáng",
    "显示": "Hiển thị", "声音": "Âm thanh", "壁纸": "Hình nền", "主题": "Chủ đề",
    "更新": "Cập nhật", "安装": "Cài đặt", "卸载": "Gỡ cài đặt", "打开": "Mở",
    "选择": "Chọn", "全部": "Tất cả", "其他": "Khác", "默认": "Mặc định",
    "自动": "Tự động", "手动": "Thủ công", "是": "Có", "否": "Không",
    "知道了": "Đã hiểu", "重试": "Thử lại", "跳过": "Bỏ qua", "继续": "Tiếp tục",
    "暂停": "Tạm dừng", "播放": "Phát", "上一首": "Bài trước", "下一首": "Bài sau",
    "播放列表": "Danh sách phát", "收藏": "Yêu thích", "历史": "Lịch sử",
    "消息": "Tin nhắn", "通知": "Thông báo", "相册": "Album", "照片": "Ảnh",
    "录制": "Ghi", "回放": "Phát lại", "锁定": "Khóa", "解锁": "Mở khóa",
    "车速": "Tốc độ", "里程": "Số km", "油耗": "Tiêu hao", "能耗": "Tiêu thụ điện",
    "驾驶": "Lái xe", "泊车": "Đỗ xe", "倒车": "Lùi xe", "雷达": "Radar",
    "氛围灯": "Đèn viền", "车窗": "Cửa sổ", "天窗": "Cửa sổ trời", "雨刷": "Gạt mưa",
    "大灯": "Đèn pha", "雾灯": "Đèn sương mù", "双闪": "Đèn khẩn cấp",
    "安全": "An toàn", "隐私": "Quyền riêng tư", "服务": "Dịch vụ", "反馈": "Phản hồi",
}

TRANSLATION_CACHE = dict(CUSTOM_GLOSSARY)
_START_TS = time.time()
_API_COUNT = 0
_CONSEC_FAILS = 0
_STOP = False
_API_DISABLED = False

CJK_REGEX = re.compile(r'[\u4e00-\u9fff]')
PLACEHOLDER_REGEX = re.compile(r'(%(\d+\$)?[-#+ 0,(]*\d*\.?\d*[sdfoxegcbh]|\{\d+\}|\\n|\\t)')
FORMAT_SPECIFIER_REGEX = re.compile(r'%(\d+\$)?[-#+ 0,(]*\d*\.?\d*[sdfoxegcbh]')

def timed_out():
    return (time.time() - _START_TS) >= MAX_TRANSLATE_SECONDS

def has_chinese(text):
    return bool(text and CJK_REGEX.search(text))

def extract_format_specifiers(text):
    return [m.group(0) for m in FORMAT_SPECIFIER_REGEX.finditer(text)]

def validate_format_specifiers(original, translated):
    return sorted(extract_format_specifiers(original)) == sorted(extract_format_specifiers(translated))

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
    if t.startswith(('http://', 'https://', 'file://', 'content://', '@string/',
                     '@drawable/', '@color/', '@style/', 'Lcom/', 'Landroid/')):
        return True
    if re.match(r'^[a-zA-Z0-9_.\-/:]+$', t):
        return True
    return False

def gtx_translate(text, sl='zh-CN', tl='vi'):
    """Unofficial Google Translate endpoint — works better on CI than deep-translator."""
    q = urllib.parse.urlencode({
        'client': 'gtx',
        'sl': sl,
        'tl': tl,
        'dt': 't',
        'q': text,
    })
    url = 'https://translate.googleapis.com/translate_a/single?' + q
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        'Accept': '*/*',
    })
    with urllib.request.urlopen(req, timeout=12) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    parts = []
    if data and data[0]:
        for seg in data[0]:
            if seg and seg[0]:
                parts.append(seg[0])
    return ''.join(parts).strip()

def translate_single(text, force_cjk_only=True):
    global _API_COUNT, _STOP, _CONSEC_FAILS, _API_DISABLED
    if _STOP or timed_out():
        _STOP = True
        return text
    if should_skip_string(text):
        return text
    if force_cjk_only and not has_chinese(text):
        return text

    clean_text = text.strip()
    if clean_text in TRANSLATION_CACHE:
        cached = TRANSLATION_CACHE[clean_text]
        if validate_format_specifiers(clean_text, cached):
            return text.replace(clean_text, cached) if clean_text != text else cached
        return text

    if _API_DISABLED or _API_COUNT >= MAX_STRINGS:
        TRANSLATION_CACHE[clean_text] = clean_text
        return text

    protected, phs = protect_placeholders(clean_text)
    # GTX limit ~ short strings; split if needed
    if len(protected) > 450:
        TRANSLATION_CACHE[clean_text] = clean_text
        return text

    for attempt in range(3):
        if timed_out():
            _STOP = True
            return text
        try:
            translated = gtx_translate(protected)
            _API_COUNT += 1
            _CONSEC_FAILS = 0
            if translated:
                restored = restore_placeholders(translated, phs)
                if validate_format_specifiers(clean_text, restored):
                    TRANSLATION_CACHE[clean_text] = restored
                    time.sleep(SLEEP_OK)
                    if _API_COUNT % BATCH_PRINT_EVERY == 0:
                        print(f"  ... API {_API_COUNT}, cache={len(TRANSLATION_CACHE)}, fails={_CONSEC_FAILS}")
                    return restored
                TRANSLATION_CACHE[clean_text] = clean_text
                return text
        except Exception as e:
            _CONSEC_FAILS += 1
            msg = str(e)[:100]
            print(f"  [api-fail #{_CONSEC_FAILS}] {msg}")
            time.sleep(SLEEP_ERR * (attempt + 1))
            if _CONSEC_FAILS >= MAX_CONSECUTIVE_FAILS:
                _API_DISABLED = True
                print(f"[!] Tắt API sau {_CONSEC_FAILS} lỗi liên tiếp — chỉ dùng glossary/cache.")
                break

    TRANSLATION_CACHE[clean_text] = clean_text
    return text

def batch_warm_cache(unique_strings):
    global _STOP
    to_translate = [s for s in unique_strings
                    if s not in TRANSLATION_CACHE and not should_skip_string(s) and has_chinese(s)]
    if not to_translate:
        return
    print(f"Dịch {len(to_translate)} chuỗi CJK (max={MAX_STRINGS}, timeout={MAX_TRANSLATE_SECONDS}s, gtx)...")
    for i, text in enumerate(to_translate):
        if _STOP or timed_out() or _API_DISABLED:
            print(f"[!] Dừng warm-cache tại {i}/{len(to_translate)}")
            break
        translate_single(text, force_cjk_only=True)
        if (i + 1) % BATCH_PRINT_EVERY == 0:
            print(f"  warm-cache: {i+1}/{len(to_translate)} ({int(time.time()-_START_TS)}s)")

def fix_manifest_anti_crash(decompiled_dir, strip_shared_uid=False):
    path = os.path.join(decompiled_dir, "AndroidManifest.xml")
    if not os.path.exists(path):
        return
    print("Tối ưu AndroidManifest.xml...")
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    content = content.replace('android:extractNativeLibs="false"', 'android:extractNativeLibs="true"')
    for pat in [r'\s*android:isSplitRequired="true"', r'\s*android:requiredSplitTypes="[^"]*"',
                r'\s*android:splitTypes="[^"]*"']:
        content = re.sub(pat, '', content)
    content = re.sub(
        r'<meta-data[^>]+android:name="(?:com\.android\.vending\.splits|com\.android\.vending\.derived\.apk\.id|com\.android\.stamp\.source|com\.android\.stamp\.type)"[^>]*/?>',
        '', content, flags=re.IGNORECASE)
    if strip_shared_uid:
        content = re.sub(r'\s*android:sharedUserId="[^"]*"', '', content)
        content = re.sub(r'\s*android:sharedUserLabel="[^"]*"', '', content)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def fix_apktool_yml(decompiled_dir):
    path = os.path.join(decompiled_dir, "apktool.yml")
    if not os.path.exists(path):
        return
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    if "doNotCompress:" in content and "- so" not in content:
        content = content.replace("doNotCompress:", "doNotCompress:\n- so")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def process_values_xml(input_path, output_path, only_chinese=True):
    if not os.path.exists(input_path):
        return
    print(f"Values: {input_path} -> {output_path}")
    try:
        tree = ET.parse(input_path)
    except Exception as e:
        print(f"  [skip] XML: {e}")
        return
    root = tree.getroot()
    warm = set()
    for elem in root.iter():
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        if tag in ('string', 'item') and elem.text and has_chinese(elem.text):
            warm.add(elem.text)
    batch_warm_cache(warm)
    for elem in root.iter():
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        if tag in ('string', 'item') and elem.text:
            if only_chinese and not has_chinese(elem.text):
                continue
            elem.text = translate_single(elem.text, force_cjk_only=only_chinese)
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    tree.write(output_path, encoding='utf-8', xml_declaration=True)

LAYOUT_ATTR_REGEX = re.compile(
    r'(android:(?:text|hint|title|summary|dialogTitle|positiveButtonText|negativeButtonText)=")([^"@][^"]*?)(")'
)

def process_layout_files(base_res_dir):
    xml_files = glob.glob(os.path.join(base_res_dir, "layout*/*.xml")) + \
                glob.glob(os.path.join(base_res_dir, "xml*/*.xml"))
    unique, matched = set(), []
    for fpath in xml_files:
        try:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            continue
        cjk = [m[1] for m in LAYOUT_ATTR_REGEX.findall(content) if has_chinese(m[1])]
        if cjk:
            unique.update(cjk)
            matched.append(fpath)
    print(f"Layout: {len(matched)} files, {len(unique)} CJK")
    batch_warm_cache(unique)
    for fpath in matched:
        if _STOP or timed_out():
            break
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        def replacer(match):
            prefix, val, suffix = match.groups()
            if has_chinese(val):
                t = translate_single(val, force_cjk_only=True)
                t = t.replace('"', '&quot;').replace("'", '&apos;').replace('<', '&lt;').replace('>', '&gt;')
                return f"{prefix}{t}{suffix}"
            return match.group(0)
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(LAYOUT_ATTR_REGEX.sub(replacer, content))

SMALI_CONST_STRING_REGEX = re.compile(r'^(\s*const-string(?:/jumbo)?\s+[vp]\d+,\s*")(.+)("\s*)$')
UNICODE_ESCAPE_REGEX = re.compile(r'\\u([0-9a-fA-F]{4})')
DANGEROUS = (
    'SharedPreferences', 'JSONObject', 'JSONArray', 'Intent;-><init>',
    'Intent;->putExtra', 'Intent;->get', 'Bundle;->put', 'Bundle;->get',
    'Class;->forName', 'Class;->getDeclared', 'Enum;->valueOf',
    'SQLiteDatabase', 'MessageDigest', 'Cipher', 'System;->loadLibrary',
)

def decode_smali_unicode(s):
    return UNICODE_ESCAPE_REGEX.sub(lambda m: chr(int(m.group(1), 16)), s)

def escape_for_smali(s):
    return s.replace('\\"', '"').replace('"', '\\"').replace('\n', '\\n').replace('\r', '')

def is_safe_smali_ui_string(s):
    return has_chinese(s) and len(s) <= 80 and not should_skip_string(s)

def process_smali_files(decompiled_dir):
    smali_dirs = glob.glob(os.path.join(decompiled_dir, "smali*"))
    if not smali_dirs:
        return
    print("Quét smali...")
    unique, targets = set(), []
    for sd in smali_dirs:
        for root, _, files in os.walk(sd):
            for name in files:
                if not name.endswith('.smali'):
                    continue
                sf = os.path.join(root, name)
                try:
                    with open(sf, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                except Exception:
                    continue
                found = False
                for idx, line in enumerate(lines):
                    m = SMALI_CONST_STRING_REGEX.match(line)
                    if not m:
                        continue
                    decoded = decode_smali_unicode(m.group(2))
                    if not is_safe_smali_ui_string(decoded):
                        continue
                    ctx = "".join(lines[idx+1:idx+5])
                    if any(d in ctx for d in DANGEROUS):
                        continue
                    unique.add(decoded)
                    found = True
                if found:
                    targets.append(sf)
                    if len(targets) >= 400:
                        break
            if len(targets) >= 400:
                break
    print(f"Smali: {len(targets)} files, {len(unique)} candidates")
    batch_warm_cache(unique)
    for sf in targets:
        if _STOP or timed_out() or _API_DISABLED:
            break
        with open(sf, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        out = []
        for idx, line in enumerate(lines):
            m = SMALI_CONST_STRING_REGEX.match(line)
            if m:
                prefix, raw, suffix = m.groups()
                decoded = decode_smali_unicode(raw)
                if is_safe_smali_ui_string(decoded):
                    ctx = "".join(lines[idx+1:idx+5])
                    if not any(d in ctx for d in DANGEROUS):
                        line = f"{prefix}{escape_for_smali(translate_single(decoded, True))}{suffix}\n"
            out.append(line)
        with open(sf, 'w', encoding='utf-8') as f:
            f.writelines(out)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="decompiled_apk")
    parser.add_argument("--strip-shared-uid", action="store_true")
    parser.add_argument("--skip-smali", action="store_true")
    parser.add_argument("--max-strings", type=int, default=3000)
    parser.add_argument("--timeout-min", type=int, default=25)
    args = parser.parse_args()

    g = globals()
    g["MAX_STRINGS"] = args.max_strings
    g["MAX_TRANSLATE_SECONDS"] = args.timeout_min * 60
    g["_START_TS"] = time.time()
    g["_API_COUNT"] = 0
    g["_CONSEC_FAILS"] = 0
    g["_STOP"] = False
    g["_API_DISABLED"] = False

    ddir = args.dir
    base_res = os.path.join(ddir, "res")
    print(f"=== Deep Viet Hoa GTX | max={args.max_strings} timeout={args.timeout_min}m skip_smali={args.skip_smali} ===")
    # smoke test API
    try:
        t = gtx_translate("设置")
        print(f"API smoke OK: 设置 -> {t}")
    except Exception as e:
        print(f"API smoke FAIL: {e}")
        print("Sẽ chỉ dùng glossary offline.")
        g["_API_DISABLED"] = True

    fix_manifest_anti_crash(ddir, strip_shared_uid=args.strip_shared_uid)
    fix_apktool_yml(ddir)

    for xml_name in ["strings.xml", "arrays.xml", "plurals.xml"]:
        default_file = os.path.join(base_res, f"values/{xml_name}")
        vi_file = os.path.join(base_res, f"values-vi/{xml_name}")
        if os.path.exists(default_file):
            process_values_xml(default_file, vi_file, only_chinese=True)
            process_values_xml(default_file, default_file, only_chinese=True)
        for zh_dir in ["values-zh", "values-zh-rCN", "values-zh-rTW", "values-zh-rHK"]:
            zh_file = os.path.join(base_res, f"{zh_dir}/{xml_name}")
            if os.path.exists(zh_file):
                process_values_xml(zh_file, zh_file, only_chinese=True)
                if not os.path.exists(vi_file):
                    process_values_xml(zh_file, vi_file, only_chinese=True)

    if os.path.exists(base_res):
        process_layout_files(base_res)

    if not args.skip_smali:
        process_smali_files(ddir)
    else:
        print("Skip smali.")

    print(f"=== DONE | API={_API_COUNT} cache={len(TRANSLATION_CACHE)} t={int(time.time()-_START_TS)}s stop={_STOP} api_off={_API_DISABLED} ===")
