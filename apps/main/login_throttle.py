import time

from django.core.cache import cache

LOGIN_ATTEMPT_LIMIT = 3
LOGIN_LOCKOUT_SECONDS = 60


def _attempts_key(email: str) -> str:
    return f'login_attempts:{email.lower().strip()}'


def _lock_key(email: str) -> str:
    return f'login_lock:{email.lower().strip()}'


def get_lockout_seconds_remaining(email: str) -> int:
    locked_until = cache.get(_lock_key(email))
    if locked_until is None:
        return 0
    remaining = int(locked_until - time.time())
    if remaining <= 0:
        clear_login_attempts(email)
        return 0
    return remaining


def is_login_locked(email: str) -> bool:
    return get_lockout_seconds_remaining(email) > 0


def lockout_error_message(email: str) -> str:
    remaining = get_lockout_seconds_remaining(email)
    minutes = max(1, (remaining + 59) // 60)
    if minutes == 1:
        return (
            f'Excedeu o limite de {LOGIN_ATTEMPT_LIMIT} tentativas de login. '
            'Aguarde 1 minuto antes de tentar novamente.'
        )
    return (
        f'Excedeu o limite de {LOGIN_ATTEMPT_LIMIT} tentativas de login. '
        f'Aguarde {minutes} minutos antes de tentar novamente.'
    )


def failed_login_error_message(email: str, attempts: int) -> str:
    remaining = max(0, LOGIN_ATTEMPT_LIMIT - attempts)
    if remaining <= 0:
        return lockout_error_message(email)
    if remaining == 1:
        return 'Email ou senha inválidos. Resta 1 tentativa antes do bloqueio temporário.'
    return f'Email ou senha inválidos. Restam {remaining} tentativas antes do bloqueio temporário.'


def register_failed_login(email: str) -> tuple[int, bool]:
    normalized_email = email.lower().strip()
    attempts_key = _attempts_key(normalized_email)
    attempts = cache.get(attempts_key, 0) + 1
    cache.set(attempts_key, attempts, timeout=LOGIN_LOCKOUT_SECONDS)

    if attempts >= LOGIN_ATTEMPT_LIMIT:
        cache.set(
            _lock_key(normalized_email),
            time.time() + LOGIN_LOCKOUT_SECONDS,
            timeout=LOGIN_LOCKOUT_SECONDS,
        )
        return attempts, True

    return attempts, False


def clear_login_attempts(email: str) -> None:
    normalized_email = email.lower().strip()
    cache.delete(_attempts_key(normalized_email))
    cache.delete(_lock_key(normalized_email))
