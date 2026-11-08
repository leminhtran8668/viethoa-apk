#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deep Viet Hoa APK + Anti-Crash — OFFLINE (glossary + cache JSON).
Nhanh, ổn định trên CI, không phụ thuộc Google API.
"""

import os, re, sys, glob, json, argparse, time
import xml.etree.ElementTree as ET

CACHE_PATH_DEFAULT = os.path.join(os.path.dirname(__file__), "translation_cache.json")

# Thuật ngữ UI / ô tô thường gặp
GLOSSARY = {
    "确定": "Xác nhận", "取消": "Hủy", "设置": "Cài đặt", "系统设置": "Cài đặt hệ thống",
    "蓝牙": "Bluetooth", "行车记录仪": "Cam hành trình", "摄像头": "Camera",
    "车门": "Cửa xe", "左前门": "Cửa trước trái", "右前门": "Cửa trước phải",
    "左后门": "Cửa sau trái", "右后门": "Cửa sau phải", "后备箱": "Cốp xe",
    "引擎盖": "Nắp capo", "音量": "Âm lượng", "静音": "Tắt tiếng", "密码": "Mật khẩu",
    "提示": "Thông báo", "警告": "Cảnh báo", "成功": "Thành công", "失败": "Thất bại",
    "正在加载": "Đang tải...", "请稍候": "Vui lòng chờ...", "退出": "Thoát", "保存": "Lưu",
    "开启": "Bật", "关闭": "Tắt", "已开启": "Đã bật", "已关闭": "Đã tắt",
    "打开": "Mở", "主页": "Trang chủ", "返回": "Quay lại", "刷新": "Làm mới",
    "删除": "Xóa", "清空": "Xóa sạch", "版本": "Phiên bản", "权限": "Quyền truy cập",
    "开始": "Bắt đầu", "结束": "Kết thúc", "下一步": "Tiếp theo", "上一步": "Quay lại",
    "完成": "Hoàn tất", "搜索": "Tìm kiếm", "帮助": "Trợ giúp", "关于": "Giới thiệu",
    "语言": "Ngôn ngữ", "中文": "Tiếng Trung", "英文": "Tiếng Anh", "越南语": "Tiếng Việt",
    "导航": "Điều hướng", "地图": "Bản đồ", "音乐": "Nhạc", "视频": "Video",
    "电话": "Điện thoại", "信息": "Tin nhắn", "应用": "Ứng dụng", "文件": "Tệp",
    "下载": "Tải xuống", "上传": "Tải lên", "连接": "Kết nối", "断开": "Ngắt kết nối",
    "温度": "Nhiệt độ", "空调": "Điều hòa", "座椅": "Ghế", "方向盘": "Vô lăng",
    "胎压": "Áp suất lốp", "续航": "Quãng đường", "电量": "Pin", "充电": "Sạc",
    "登录": "Đăng nhập", "注册": "Đăng ký", "用户": "Người dùng", "账户": "Tài khoản",
    "网络": "Mạng", "无线": "Không dây", "热点": "Điểm phát sóng", "亮度": "Độ sáng",
    "显示": "Hiển thị", "声音": "Âm thanh", "壁纸": "Hình nền", "主题": "Chủ đề",
    "更新": "Cập nhật", "安装": "Cài đặt", "卸载": "Gỡ cài đặt", "选择": "Chọn",
    "全部": "Tất cả", "其他": "Khác", "默认": "Mặc định", "自动": "Tự động",
    "手动": "Thủ công", "是": "Có", "否": "Không", "知道了": "Đã hiểu",
    "重试": "Thử lại", "跳过": "Bỏ qua", "继续": "Tiếp tục", "暂停": "Tạm dừng",
    "播放": "Phát", "上一首": "Bài trước", "下一首": "Bài sau", "播放列表": "Danh sách phát",
    "收藏": "Yêu thích", "历史": "Lịch sử", "消息": "Tin nhắn", "通知": "Thông báo",
    "相册": "Album", "照片": "Ảnh", "录制": "Ghi", "回放": "Phát lại",
    "锁定": "Khóa", "解锁": "Mở khóa", "车速": "Tốc độ", "里程": "Số km",
    "油耗": "Tiêu hao", "能耗": "Tiêu thụ điện", "驾驶": "Lái xe", "泊车": "Đỗ xe",
    "倒车": "Lùi xe", "雷达": "Radar", "氛围灯": "Đèn viền", "车窗": "Cửa sổ",
    "天窗": "Cửa sổ trời", "雨刷": "Gạt mưa", "大灯": "Đèn pha", "雾灯": "Đèn sương mù",
    "双闪": "Đèn khẩn cấp", "安全": "An toàn", "隐私": "Quyền riêng tư",
    "服务": "Dịch vụ", "反馈": "Phản hồi", "加载中": "Đang tải", "请输入": "Vui lòng nhập",
    "姓名": "Họ tên", "时间": "Thời gian", "日期": "Ngày", "小时": "Giờ", "分钟": "Phút",
    "秒": "Giây", "年": "Năm", "月": "Tháng", "日": "Ngày", "周": "Tuần",
    "今天": "Hôm nay", "昨天": "Hôm qua", "明天": "Ngày mai", "上午": "Sáng",
    "下午": "Chiều", "晚上": "Tối", "更多": "Thêm", "详情": "Chi tiết",
    "列表": "Danh sách", "添加": "Thêm", "编辑": "Sửa", "修改": "Chỉnh sửa",
    "提交": "Gửi", "发送": "Gửi", "接收": "Nhận", "复制": "Sao chép",
    "粘贴": "Dán", "剪切": "Cắt", "分享": "Chia sẻ", "推荐": "Đề xuất",
    "热门": "Phổ biến", "最新": "Mới nhất", "全部应用": "Tất cả ứng dụng",
    "系统": "Hệ thống", "车辆": "Xe", "驾驶模式": "Chế độ lái",
    "经济": "Tiết kiệm", "舒适": "Thoải mái", "运动": "Thể thao",
    "标准": "Tiêu chuẩn", "雪地": "Tuyết", "沙地": "Cát", "泥地": "Bùn",
    "电池": "Pin", "电机": "Động cơ điện", "功率": "Công suất",
    "电压": "Điện áp", "电流": "Dòng điện", "剩余": "Còn lại",
    "总里程": "Tổng quãng đường", "平均": "Trung bình", "最大": "Tối đa",
    "最小": "Tối thiểu", "当前": "Hiện tại", "状态": "Trạng thái",
    "正常": "Bình thường", "异常": "Bất thường", "故障": "Lỗi",
    "检修": "Bảo dưỡng", "保养": "Bảo dưỡng", "重置": "Đặt lại",
    "恢复出厂": "Khôi phục máy", "重启": "Khởi động lại", "关机": "Tắt máy",
    "同意": "Đồng ý", "拒绝": "Từ chối", "允许": "Cho phép", "禁止": "Cấm",
    "开启中": "Đang bật", "关闭中": "Đang tắt", "连接中": "Đang kết nối",
    "已连接": "Đã kết nối", "未连接": "Chưa kết nối", "可用": "Khả dụng",
    "不可用": "Không khả dụng", "无数据": "Không có dữ liệu", "未知": "Không rõ",
    "错误": "Lỗi", "操作成功": "Thành công", "操作失败": "Thất bại",
    "网络错误": "Lỗi mạng", "超时": "Hết thời gian", "重连": "Kết nối lại",
    "WIFI": "Wi‑Fi", "WiFi": "Wi‑Fi", "GPS": "GPS", "USB": "USB",
    "SD卡": "Thẻ SD", "存储": "Lưu trữ", "内存": "Bộ nhớ", "清理": "Dọn dẹp",
    "加速": "Tăng tốc", "省电": "Tiết kiệm pin", "性能": "Hiệu năng",
    "开发者": "Nhà phát triển", "调试": "Gỡ lỗi", "日志": "Nhật ký",
    "截图": "Chụp màn hình", "录屏": "Ghi màn hình", "投屏": "Chiếu màn hình",
    "分屏": "Chia màn hình", "全屏": "Toàn màn hình", "横屏": "Ngang",
    "竖屏": "Dọc", "旋转": "Xoay", "镜像": "Gương",
    "前排": "Hàng trước", "后排": "Hàng sau", "主驾": "Ghế lái",
    "副驾": "Ghế phụ", "左侧": "Bên trái", "右侧": "Bên phải",
    "内部": "Trong xe", "外部": "Ngoài xe", "车内": "Trong cabin",
    "车外": "Bên ngoài", "儿童锁": "Khóa trẻ em", "中控锁": "Khóa trung tâm",
    "尾门": "Cốp điện", "加油口": "Nắp bình", "充电口": "Cổng sạc",
    "慢充": "Sạc chậm", "快充": "Sạc nhanh", "预约充电": "Hẹn giờ sạc",
    "充电中": "Đang sạc", "已充满": "Đã đầy", "未充电": "Chưa sạc",
    "能耗管理": "Quản lý năng lượng", "驾驶习惯": "Thói quen lái",
    "行程": "Hành trình", "本次": "Chuyến này", "累计": "Tích lũy",
    "单位": "Đơn vị", "公里": "Km", "英里": "Dặm", "摄氏度": "°C",
    "华氏度": "°F", "气压": "Áp suất khí", "海拔": "Độ cao",
    "天气": "Thời tiết", "晴": "Nắng", "雨": "Mưa", "雪": "Tuyết",
    "雾": "Sương mù", "空气质量": "Chất lượng không khí",
    "空气净化器": "Máy lọc không khí", "香氛": "Nước hoa xe",
    "座椅加热": "Sưởi ghế", "座椅通风": "Thông gió ghế",
    "方向盘加热": "Sưởi vô lăng", "后视镜": "Gương chiếu hậu",
    "后视镜加热": "Sưởi gương", "自动折叠": "Tự gập",
    "感应雨刷": "Gạt mưa cảm biến", "自动大灯": "Đèn pha tự động",
    "迎宾灯": "Đèn chào", "氛围": "Không khí", "颜色": "Màu",
    "模式": "Chế độ", "场景": "Cảnh", "露营": "Cắm trại",
    "休息": "Nghỉ ngơi", "宠物": "Thú cưng", "哨兵": "Canh gác",
    "隐私模式": "Chế độ riêng tư", "勿扰": "Không làm phiền",
    "勿扰模式": "Chế độ không làm phiền", "夜间": "Ban đêm",
    "白天": "Ban ngày", "自适应": "Tự thích ứng",
}

CJK_REGEX = re.compile(r'[\u4e00-\u9fff]')
PLACEHOLDER_REGEX = re.compile(r'(%(\d+\$)?[-#+ 0,(]*\d*\.?\d*[sdfoxegcbh]|\{\d+\}|\\n|\\t)')
FORMAT_SPECIFIER_REGEX = re.compile(r'%(\d+\$)?[-#+ 0,(]*\d*\.?\d*[sdfoxegcbh]')
LAYOUT_ATTR_REGEX = re.compile(
    r'(android:(?:text|hint|title|summary|dialogTitle|positiveButtonText|negativeButtonText)=")([^"@][^"]*?)(")'
)
SMALI_CONST_STRING_REGEX = re.compile(r'^(\s*const-string(?:/jumbo)?\s+[vp]\d+,\s*")(.+)("\s*)$')
UNICODE_ESCAPE_REGEX = re.compile(r'\\u([0-9a-fA-F]{4})')
DANGEROUS = (
    'SharedPreferences', 'JSONObject', 'JSONArray', 'Intent;-><init>',
    'Intent;->putExtra', 'Intent;->get', 'Bundle;->put', 'Bundle;->get',
    'Class;->forName', 'Class;->getDeclared', 'Enum;->valueOf',
    'SQLiteDatabase', 'MessageDigest', 'Cipher', 'System;->loadLibrary',
)

CACHE = {}
STATS = {"hit": 0, "miss": 0, "glossary": 0}


def has_chinese(text):
    return bool(text and CJK_REGEX.search(text))


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


def load_cache(path):
    global CACHE
    CACHE = dict(GLOSSARY)
    if path and os.path.isfile(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict):
                CACHE.update({str(k): str(v) for k, v in data.items() if v})
                print(f"Đã nạp cache: {len(data)} mục từ {path}")
        except Exception as e:
            print(f"[!] Không đọc được cache: {e}")
    print(f"Tổng từ điển+cache: {len(CACHE)}")


def save_cache(path):
    # Chỉ lưu phần không nằm trong glossary gốc (user/extended)
    extra = {k: v for k, v in CACHE.items() if k not in GLOSSARY and has_chinese(k)}
    try:
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(extra, f, ensure_ascii=False, indent=1, sort_keys=True)
        print(f"Đã ghi cache mở rộng: {len(extra)} mục -> {path}")
    except Exception as e:
        print(f"[!] Không ghi cache: {e}")


def escape_android_string(s):
    """Escape ký tự phá Android strings.xml / aapt (an toàn với ElementTree)."""
    if s is None:
        return s
    s = s.replace('&', '&amp;')
    s = s.replace('<', '&lt;')
    s = s.replace('>', '&gt;')
    s = s.replace("'", "&apos;")
    s = s.replace('"', "&quot;")
    return s


def translate_text(text):
    """Offline lookup only. Giữ nguyên nếu không có trong từ điển/cache."""
    if should_skip_string(text) or not has_chinese(text):
        return text
    clean = text.strip()
    if clean in CACHE:
        STATS["hit"] += 1
        if clean in GLOSSARY:
            STATS["glossary"] += 1
        cached = CACHE[clean]
        return text.replace(clean, cached) if clean != text else cached
    # Thử exact substring dài (câu chứa đúng 1 key)
    if clean in GLOSSARY:
        STATS["glossary"] += 1
        return GLOSSARY[clean]
    STATS["miss"] += 1
    return text


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


def process_values_xml(input_path, output_path):
    if not os.path.exists(input_path):
        return
    print(f"Values: {input_path}")
    try:
        tree = ET.parse(input_path)
    except Exception as e:
        print(f"  [skip] {e}")
        return
    root = tree.getroot()
    n = 0
    for elem in root.iter():
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        if tag in ('string', 'item') and elem.text and has_chinese(elem.text):
            new = translate_text(elem.text)
            if new != elem.text:
                elem.text = escape_android_string(new)
                n += 1
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    tree.write(output_path, encoding='utf-8', xml_declaration=True)
    print(f"  -> đổi {n} chuỗi")


def process_layout_files(base_res_dir):
    xml_files = glob.glob(os.path.join(base_res_dir, "layout*/*.xml")) + \
                glob.glob(os.path.join(base_res_dir, "xml*/*.xml"))
    changed_files = 0
    for fpath in xml_files:
        try:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            continue
        if not has_chinese(content):
            continue

        def replacer(match):
            prefix, val, suffix = match.groups()
            if has_chinese(val):
                t = escape_android_string(translate_text(val))
                return f"{prefix}{t}{suffix}"
            return match.group(0)

        new_content = LAYOUT_ATTR_REGEX.sub(replacer, content)
        if new_content != content:
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            changed_files += 1
    print(f"Layout/XML: chỉnh {changed_files} file")


def decode_smali_unicode(s):
    return UNICODE_ESCAPE_REGEX.sub(lambda m: chr(int(m.group(1), 16)), s)


def escape_for_smali(s):
    return s.replace('\\"', '"').replace('"', '\\"').replace('\n', '\\n').replace('\r', '')


def process_smali_files(decompiled_dir):
    smali_dirs = glob.glob(os.path.join(decompiled_dir, "smali*"))
    if not smali_dirs:
        return
    changed = 0
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
                out, mod = [], False
                for idx, line in enumerate(lines):
                    m = SMALI_CONST_STRING_REGEX.match(line)
                    if m:
                        prefix, raw, suffix = m.groups()
                        decoded = decode_smali_unicode(raw)
                        if has_chinese(decoded) and len(decoded) <= 80 and not should_skip_string(decoded):
                            ctx = "".join(lines[idx+1:idx+5])
                            if not any(d in ctx for d in DANGEROUS):
                                tr = translate_text(decoded)
                                if tr != decoded:
                                    line = f"{prefix}{escape_for_smali(tr)}{suffix}\n"
                                    mod = True
                    out.append(line)
                if mod:
                    with open(sf, 'w', encoding='utf-8') as f:
                        f.writelines(out)
                    changed += 1
    print(f"Smali: chỉnh {changed} file")


def export_misses(decompiled_dir, out_path):
    """Quét chuỗi CJK chưa có trong cache — để bổ sung từ điển sau."""
    misses = set()
    base_res = os.path.join(decompiled_dir, "res")
    for xml_name in ["strings.xml", "arrays.xml", "plurals.xml"]:
        for folder in ["values", "values-zh", "values-zh-rCN", "values-zh-rTW"]:
            path = os.path.join(base_res, folder, xml_name)
            if not os.path.isfile(path):
                continue
            try:
                tree = ET.parse(path)
            except Exception:
                continue
            for elem in tree.getroot().iter():
                tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                if tag in ('string', 'item') and elem.text and has_chinese(elem.text):
                    c = elem.text.strip()
                    if c not in CACHE and not should_skip_string(c):
                        misses.add(c)
    data = {m: "" for m in sorted(misses, key=len)}
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"Chuỗi chưa dịch (miss): {len(data)} -> {out_path}")


if __name__ == "__main__":
    t0 = time.time()
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="decompiled_apk")
    parser.add_argument("--strip-shared-uid", action="store_true")
    parser.add_argument("--skip-smali", action="store_true")
    parser.add_argument("--cache", default=CACHE_PATH_DEFAULT)
    args = parser.parse_args()

    print("=== Deep Viet Hoa OFFLINE (glossary + cache) ===")
    load_cache(args.cache)

    ddir = args.dir
    base_res = os.path.join(ddir, "res")
    fix_manifest_anti_crash(ddir, strip_shared_uid=args.strip_shared_uid)
    fix_apktool_yml(ddir)

    for xml_name in ["strings.xml", "arrays.xml", "plurals.xml"]:
        default_file = os.path.join(base_res, f"values/{xml_name}")
        vi_file = os.path.join(base_res, f"values-vi/{xml_name}")
        if os.path.exists(default_file):
            process_values_xml(default_file, vi_file)
            process_values_xml(default_file, default_file)
        for zh_dir in ["values-zh", "values-zh-rCN", "values-zh-rTW", "values-zh-rHK"]:
            zh_file = os.path.join(base_res, f"{zh_dir}/{xml_name}")
            if os.path.exists(zh_file):
                process_values_xml(zh_file, zh_file)
                if not os.path.exists(vi_file):
                    process_values_xml(zh_file, vi_file)

    if os.path.exists(base_res):
        process_layout_files(base_res)

    if not args.skip_smali:
        process_smali_files(ddir)
    else:
        print("Skip smali.")

    miss_path = os.path.join("output", "untranslated_zh.json")
    os.makedirs("output", exist_ok=True)
    export_misses(ddir, miss_path)
    save_cache(args.cache)

    print(f"=== DONE | hit={STATS['hit']} glossary={STATS['glossary']} miss={STATS['miss']} t={int(time.time()-t0)}s ===")
