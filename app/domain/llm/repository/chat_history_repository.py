"""session_id별 최근 대화(질문, 답변)를 메모리에 보관하는 저장소. 서버를 재시작시 삭제"""
from collections import defaultdict, deque
from threading import Lock

MAX_TURNS = 5  # 프롬프트에 넣을 최근 대화 수 (질문+답변 한 쌍 = 1턴)

_histories: dict[str, deque[tuple[str, str]]] = defaultdict(lambda: deque(maxlen=MAX_TURNS))
_lock = Lock()


def get(session_id: str) -> list[tuple[str, str]]:
    with _lock:
        return list(_histories[session_id])


def add(session_id: str, question: str, answer: str) -> None:
    with _lock:
        _histories[session_id].append((question, answer))