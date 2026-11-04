"""Chroma(벡터 DB) 연결·검색 실패를 나타내는 예외.
Chroma 라이브러리의 다양한 예외를 이 하나로 바꿔서, controller가 Chroma 내부 구현을 몰라도 503으로 처리할 수 있게 한다."""


class VectorStoreUnavailableError(Exception):
    pass