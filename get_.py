import requests
import re
import os

headers_common = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

headers_img = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://cn.bing.com/"
}

# =========配置========
ESP_IP = "192.168.2.102"
API_TOKEN = "wyz123456"
DOWNLOAD_LOCAL = True   # True=保存图片到本地photos文件夹；False=跳过下载，只推送url给ESP32
# =====================

try:
    html_url = "https://cn.bing.com/"
    resp_html = requests.get(html_url, headers=headers_common, timeout=10)
    html_text = resp_html.text

    idx = html_text.find("iotdUrl")
    if idx != -1:
        print("\n====找到iotdUrl片段====")
        print(html_text[idx-100:idx+400])
    else:
        print("\n页面依旧没有iotdUrl，说明你的IP返回的是无壁纸变量的页面")

    obj = re.compile(r'var\s+iotdUrl\s*=\s*"(?P<url>https.*?)";', re.S)
    res = obj.findall(html_text)

    full_img_url = None
    if res:
        full_img_url = res[0]
        print("\n抓取到今日壁纸链接：")
        print(full_img_url)
        full_img_url = full_img_url.replace("https://ts1.tc.mm.bing.net/th", "https://cn.bing.com/th")
    else:
        print("\n⚠️首页抓取失败，改用必应XML接口兜底")
        xml_resp = requests.get("https://cn.bing.com/HPImageArchive.aspx?idx=0&n=1&mkt=zh-CN", headers=headers_common, timeout=10)
        xml_text = xml_resp.text
        m = re.search(r'<url>(.*?)</url>', xml_text)
        if m:
            rel_url = m.group(1)
            full_img_url = "https://cn.bing.com" + rel_url
            print("兜底接口拿到链接：", full_img_url)
        else:
            #兜底改用jpg格式链接
            full_img_url = "https://cn.bing.com/th?id=OHR.ColorfulCop_ZH-CN8015611442_1920x1080.jpg"

    if not full_img_url:
        raise Exception("获取壁纸链接失败")

    img_url = full_img_url.replace("_1920x1080.webp", "_1920x1080.jpg")
    print("\n处理后壁纸URL：", img_url)

    # 可选本地下载
    if DOWNLOAD_LOCAL:
        save_dir = "photos"
        os.makedirs(save_dir, exist_ok=True)
        img_resp = requests.get(img_url, headers=headers_img, timeout=10)
        print(f"\n图片响应状态码: {img_resp.status_code}")
        if img_resp.status_code == 200:
            save_path = os.path.join(save_dir, "test.jpg")
            with open(save_path, "wb") as f:
                f.write(img_resp.content)
            print(f"下载完成：{save_path}")
        else:
            print(f"图片下载失败，状态码：{img_resp.status_code}")

    # 推送给ESP32
    params_data = {
        "token": API_TOKEN,
        "url": img_url
    }
    print(f"\n准备请求ESP32: http://{ESP_IP}/seturl , params={params_data}")
    resp = requests.get(f"http://{ESP_IP}/seturl", params=params_data, timeout=10)
    print("ESP32返回：", resp.text)

except requests.exceptions.RequestException as e:
    print(f"\n❌网络请求异常：{e}")
except Exception as e:
    print(f"\n❌程序异常：{e}")
