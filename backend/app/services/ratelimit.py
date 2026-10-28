"""Limitador simple de tasa de solicitudes (por IP y por endpoint).

Implementación en memoria, adecuada para un proceso único (la demo local).
Antes de escalar a varias instancias debe migrarse a un almacén compartido
(Redis, por ejemplo). No sustituye a un WAF ni a un límite global de proxy.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

Hits = dict[str, deque]


class RateLimiter:
    """Ventana fija por clave. Lanza 429 cuando se supera el límite."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: Hits = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] > self.window_seconds:
                hits.popleft()
            if len(hits) >= self.max_requests:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "message": (
                            "Se superó el límite de envíos. Esperá unos minutos "
                            "y volvé a intentar."
                        )
                    },
                )
            hits.append(now)

    @staticmethod
    def client_key(request: Request, bucket: str = "default") -> str:
        host = request.client.host if request.client else "unknown"
        return f"{bucket}:{host}"

    def check_request(self, request: Request, bucket: str = "default") -> None:
        self.check(self.client_key(request, bucket))


# Límites de los formularios y del login (por IP).
login_limiter = RateLimiter(max_requests=8, window_seconds=60)
inquiry_limiter = RateLimiter(max_requests=8, window_seconds=60)
form_limiter = RateLimiter(max_requests=5, window_seconds=60)
