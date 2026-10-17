import os
import time
import json
from datetime import datetime
from difflib import SequenceMatcher
import requests
import feedparser
from openai import OpenAI
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")

if not SUPABASE_URL or not SUPABASE_KEY or not LLM_API_KEY:
    raise ValueError("环境变量未完整配置")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)

def find_similar_event(title: str, threshold: float = 0.65):
    """
    检查当前标题与数据库中已有事件标题的相似度
    若相似度超过阈值，返回已有事件的 id，否则返回 None
    """
    try:
        res = supabase.table("events").select("id, summary_title").order("id", desc=True).limit(50).execute()
        if not res.data:
            return None
        
        for event in res.data:
            existing_title = event["summary_title"]
            similarity = SequenceMatcher(None, title, existing_title).ratio()
            if similarity >= threshold:
                print(f"-> 命中相似事件 (相似度: {similarity:.2f}): [{existing_title}]")
                return event["id"]
    except Exception as e:
        print(f"相似度比对异常: {e}")
    
    return None

def process_and_aggregate(raw_id, title, content):
    """利用 LLM 对快讯进行分析、分类并生成聚合卡片"""
    prompt = f"""
    请将以下 Web3 行业快讯提炼为标准的聚合卡片格式。
    标题: {title}
    内容: {content}
    
    请输出严格的 JSON 格式（不要包含 markdown 代码块包裹）：
    {{
      "summary_title": "精炼的中文标准标题（20字以内）",
      "summary_content": "客观、严谨、结构化的中文摘要（50字左右）",
      "category": "分类（从以下选一：DeFi, Layer2, Regulation, Security, NFT, Macro, Other）"
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # 写入 events 表
        event_res = supabase.table("events").insert({
            "summary_title": result["summary_title"],
            "summary_content": result["summary_content"],
            "category": result["category"]
        }).execute()
        
        if event_res.data:
            event_id = event_res.data[0]["id"]
            # 关联 raw_feeds 与 events
            supabase.table("event_feed_mappings").insert({
                "event_id": event_id,
                "feed_id": raw_id
            }).execute()
            print(f"成功聚合事件: {result['summary_title']}")
            
        time.sleep(12)
        
    except Exception as e:
        print(f"LLM 处理失败: {e}")
        if "429" in str(e):
            print("触发频率限制，额外暂停 15 秒...")
            time.sleep(15)

# 目标 RSS 源配置
RSS_SOURCES = {
    "Odaily": "https://rss.odaily.news/rss/newsflash",
    "Cointelegraph": "https://cointelegraph.com/rss",
    "CoinDesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "Decrypt": "https://decrypt.co/feed",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def fetch_rss_feeds():
    for source_name, url in RSS_SOURCES.items():
        print(f"正在抓取 {source_name}...")
        try:
            res = requests.get(url, headers=HEADERS, timeout=15)
            res.raise_for_status()
            
            feed = feedparser.parse(res.text)
            print(f"-> 【调试】{source_name} 解析成功，共拿到 {len(feed.entries)} 条原始数据")
            
            for entry in feed.entries[:2]:
                title = entry.get("title", "")
                link = entry.get("link", "")
                summary = entry.get("summary", title)
                
                # 1. 检查 URL 基础去重
                existing = supabase.table("raw_feeds").select("id").eq("original_url", link).execute()
                if existing.data:
                    print(f"-> URL已存在，跳过: {title}")
                    continue
                
                print(f"发现新内容: {title}")
                
                # 2. 写入 raw_feeds 获取 raw_id
                raw_res = supabase.table("raw_feeds").insert({
                    "source_name": source_name,
                    "original_title": title,
                    "original_content": summary,
                    "original_url": link,
                    "published_at": datetime.now().isoformat()
                }).execute()
                
                if not raw_res.data:
                    continue
                    
                raw_id = raw_res.data[0]["id"]
                
                # 3. 语义相似度检查（多源聚合去重）
                matched_event_id = find_similar_event(title, threshold=0.65)
                
                if matched_event_id:
                    supabase.table("event_feed_mappings").insert({
                        "event_id": matched_event_id,
                        "feed_id": raw_id
                    }).execute()
                    print(f"-> 已成功归入现有事件 (ID: {matched_event_id})")
                else:
                    process_and_aggregate(raw_id, title, summary)
                    
        except Exception as e:
            print(f"抓取 {source_name} 失败: {e}")

if __name__ == "__main__":
    fetch_rss_feeds()