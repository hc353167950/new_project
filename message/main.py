import os
import argparse
from datetime import datetime
from typing import Any, Dict, List, Optional

from message.http import make_session
from message.logger import setup_logger

# Import domain functions (assumed to be pure functions or to be migrated)
from message.almanac import get_laohuangli
from message.dlt_ssq_script import default_result
from message.weather import get_weather

logger = setup_logger(__name__)

def parse_lottery_result(result: Any) -> Dict[str, List[str]]:
    """
    Normalize lottery result into a mapping: {lottery_type: [lines...]}
    Accepts string (lines separated by \n) or list of strings.
    """
    lottery_data: Dict[str, List[str]] = {}

    if not result:
        return lottery_data

    lines: List[str]
    if isinstance(result, str):
        lines = [line.strip() for line in result.splitlines() if line.strip()]
    elif isinstance(result, list):
        lines = [str(item).strip() for item in result if str(item).strip()]
    else:
        logger.warning("Unknown lottery result type: %s", type(result))
        return lottery_data

    for lotto in lines:
        if " - " in lotto:
            lottery_type = lotto.split(" - ", 1)[0]
            lottery_data.setdefault(lottery_type, []).append(lotto)
        else:
            logger.warning("Lottery line has unexpected format and will be kept raw: %s", lotto)
            lottery_data.setdefault("unknown", []).append(lotto)

    return lottery_data

def generate_daily_report(
    today_date: str,
    result_lotto: Any,
    result_weather: Any,
    laohuangli_data: Any,
) -> str:
    report = f"📅 今日时间：{today_date}\n\n"

    # 彩票部分
    lottery_data = parse_lottery_result(result_lotto)
    if lottery_data:
        for lottery_type, items in lottery_data.items():
            report += f"🎰 已为您生成今日份 {lottery_type} {len(items)}注：\n"
            for item in items:
                report += f"{item}\n"
            report += "\n"
    else:
        report += "🎰 今日无彩票数据\n\n"

    # 天气部分
    if result_weather:
        report += "🌤️ 今日天气：\n"
        if isinstance(result_weather, list):
            for w in result_weather:
                report += f"{w}\n"
        else:
            report += f"{result_weather}\n"
        report += "\n"

    # 老黄历部分
    report += "📜 今日老黄历：\n"
    if laohuangli_data:
        if isinstance(laohuangli_data, dict):
            for key, value in laohuangli_data.items():
                report += f"{key}：{value}\n"
        else:
            report += f"{laohuangli_data}\n"

    return report

def send_to_wechat(content: str, session=None, timeout: int = 10) -> bool:
    """
    Send message via Server酱 (sctapi.ftqq.com). Returns True on success.
    Uses provided requests.Session (or creates a lightweight one if None).
    """
    sckey = os.getenv("SERVERCHAN_SCKEY")
    if not sckey:
        logger.error("SERVERCHAN_SCKEY is not set; cannot send message.")
        return False

    url = f"https://sctapi.ftqq.com/{sckey}.send"
    data = {"title": "每日信息推送", "desp": content}

    sess = session or make_session()
    try:
        resp = sess.post(url, data=data, timeout=timeout)
        resp.raise_for_status()
    except Exception as exc:
        logger.exception("Failed to send message to Server酱: %s", exc)
        return False

    try:
        payload = resp.json()
    except Exception:
        logger.warning("Response is not JSON; status=%s text=%s", resp.status_code, resp.text)
        return False

    # Server酱 successful response typically contains code == 0
    if payload.get("code") == 0:
        logger.info("Message sent successfully.")
        return True
    else:
        logger.error("Server酱 returned error: %s", payload)
        return False

def collect_data(count: int, session=None) -> Dict[str, Any]:
    """
    Collect data by calling existing functions. Keep wrapper so we can later pass session
    into the called functions once they accept a session.
    """
    logger.debug("Collecting data: count=%s", count)
    # NOTE: currently default_result, get_weather, get_laohuangli may not accept session;
    # we call them as-is. Later, refactor those functions to accept session.
    try:
        lotto = default_result(count)
    except Exception:
        logger.exception("Failed to get lottery result")
        lotto = None

    try:
        weather = get_weather()
    except Exception:
        logger.exception("Failed to get weather")
        weather = None

    try:
        laohuangli = get_laohuangli()
    except Exception:
        logger.exception("Failed to get laohuangli")
        laohuangli = None

    return {"lotto": lotto, "weather": weather, "laohuangli": laohuangli}

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="生成并推送每日报告（Server酱）")
    parser.add_argument("--count", "-c", type=int, default=5, help="请求的彩票注数（传给 default_result）")
    parser.add_argument(
        "--send",
        action="store_true",
        help="将生成的报告发送到 Server酱；默认仅打印到 stdout（便于测试）",
    )
    args = parser.parse_args(argv)

    session = make_session()
    today_date = datetime.now().strftime("%Y-%m-%d")

    data = collect_data(args.count, session=session)
    report = generate_daily_report(today_date, data["lotto"], data["weather"], data["laohuangli"])\n
    # 输出报告到 stdout（用于调试/测试）
    print(report)

    if args.send:
        success = send_to_wechat(report, session=session)
        if not success:
            logger.error("Sending failed.")
            return 2

    return 0

if __name__ == "__main__":
    raise SystemExit(main())