import requests
import feedparser

# 候选 Web3 资讯源
CANDIDATE_SOURCES = {
    "Odaily": "https://rss.odaily.news/rss/newsflash",
    "PANews": "https://www.panewslab.com/zh/rss/news.xml",
    "Cointelegraph": "https://cointelegraph.com/rss",
    "CoinDesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "Decrypt": "https://decrypt.co/feed",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def test_sources():
    print("开始测试候选 RSS 源...\n")
    for name, url in CANDIDATE_SOURCES.items():
        print(f"[-] 测试源: {name}")
        print(f"    URL: {url}")
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            print(f"    HTTP 状态码: {res.status_code}")
            
            if res.status_code == 200:
                feed = feedparser.parse(res.text)
                count = len(feed.entries)
                print(f"    解析结果: 成功 | 有效条目数: {count}")
                if count > 0:
                    print(f"    最新标题: {feed.entries[0].get('title', '无标题')}")
            else:
                print(f"    解析结果: 失败 (非 200 响应)")
        except Exception as e:
            print(f"    解析结果: 异常 -> {e}")
        print("-" * 50)

if __name__ == "__main__":
    test_sources()