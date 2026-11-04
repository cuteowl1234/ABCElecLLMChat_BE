from dataclasses import dataclass, asdict

from app.core.common.type.http_code import HttpStatusCode


@dataclass
class ApiError:
    status_code: int
    err_msg: str
