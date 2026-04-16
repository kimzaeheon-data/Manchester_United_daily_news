import os
from urllib.parse import quote

import feedparser
import requests
from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY가 없습니다.")

if not DISCORD_WEBHOOK_URL:
    raise ValueError("DISCORD_WEBHOOK_URL이 없습니다.")

client = OpenAI(api_key=OPENAI_API_KEY)

query = quote("Manchester United OR 맨유 OR Man Utd")
MANU_RSS = f"https://news.google.com/rss/search?q={query}&hl=en&gl=US&ceid=US:en"


def fetch_top_news(rss_url: str, max_items: int = 10) -> list[str]:
    feed = feedparser.parse(rss_url)
    articles = [entry.get("title", "").strip() for entry in feed.entries[:max_items]]
    return [a for a in articles if a]


def summarize_manu_news(articles: list[str]) -> str:
    if not articles:
        return "오늘은 가져온 맨유 관련 뉴스가 없습니다."

    news_text = "\n".join([f"{i+1}. {title}" for i, title in enumerate(articles)])

    prompt = f"""
너는 맨체스터 유나이티드 팬을 위한 뉴스 브리핑 AI 에이전트다.

아래는 맨유 관련 최신 뉴스 제목이다.

{news_text}

아래 형식만 사용해서 한국어로 정리하라.

1. 오늘의 핵심 뉴스
- 3~5개 bullet point

2. 왜 중요한가
- 2~4개 bullet point

3. 팬 관점 한 줄
- 감정이 담긴 한 줄

조건:
- 반드시 한국어
- 너무 길지 않게
- 같은 내용은 묶어서 정리
- 마크다운 기호(##, ###, ** 등)는 절대 쓰지 말 것
- 팬 계정 느낌은 살리되 과장하지 말 것
- 출력 형식의 제목 문구는 그대로 유지할 것
"""

    response = client.responses.create(
        model="gpt-4o",
        input=prompt
    )

    return response.output_text.strip()


def build_message(summary: str) -> str:
    return f"🔴 맨유 뉴스 브리핑\n\n{summary}"


def send_to_discord(message: str) -> None:
    safe_message = message[:1900]
    response = requests.post(
        DISCORD_WEBHOOK_URL,
        json={"content": safe_message},
        timeout=20,
    )
    print("디스코드 전송 상태:", response.status_code)
    print("디스코드 응답:", response.text)
    response.raise_for_status()


def main():
    articles = fetch_top_news(MANU_RSS, max_items=10)
    print("가져온 뉴스 개수:", len(articles))
    print("뉴스 샘플:", articles[:3])

    summary = summarize_manu_news(articles)
    print("\n" + summary)

    message = build_message(summary)
    send_to_discord(message)


if __name__ == "__main__":
    main()
