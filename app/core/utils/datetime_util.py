"""날짜·시간 공통 기능. 요청 기본값, 응답 시각, Swagger 예시가 같은 형식(KST)을 쓰도록 한 곳에서 관리"""
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))  # 한국 시간대(UTC+9)로 고정
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"   # 명세 형식: YYYY-MM-DD HH:mm:ss


def now_kst() -> str:
    """현재 한국 시간을 'YYYY-MM-DD HH:mm:ss' 문자열로 반환"""
    return datetime.now(KST).strftime(DATE_FORMAT)
