"""실패 응답시 {status_code, err_msg} 형식"""
from dataclasses import dataclass


@dataclass
class ApiError:
    status_code: int
    err_msg: str
