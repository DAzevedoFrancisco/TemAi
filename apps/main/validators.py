import re
from datetime import date

from django.core.exceptions import ValidationError
from django.core.validators import validate_email

MIN_NAME_LENGTH = 6
MIN_CLIENT_AGE = 14
MIN_VENDOR_AGE = 18
MOZAMBIQUE_PHONE_PREFIXES = ('82', '83', '84', '85', '86', '87')


def normalize_whitespace(value):
    return ' '.join((value or '').split())


def validate_min_name(value, *, field_label='O nome', min_length=MIN_NAME_LENGTH):
    name = normalize_whitespace(value)
    if len(name) < min_length:
        raise ValidationError(
            f'{field_label} deve ter pelo menos {min_length} caracteres.'
        )
    return name


def validate_email_address(value):
    email = (value or '').strip().lower()
    if not email:
        raise ValidationError('O email é obrigatório.')
    validate_email(email)
    return email


def extract_mozambique_phone_digits(value):
    digits = re.sub(r'\D', '', value or '')
    if digits.startswith('258'):
        digits = digits[3:]
    return digits


def is_valid_mozambique_phone_digits(digits):
    return len(digits) == 9 and digits[:2] in MOZAMBIQUE_PHONE_PREFIXES


def validate_mozambique_phone(value):
    if not value or not str(value).strip():
        raise ValidationError('O telefone é obrigatório.')

    digits = extract_mozambique_phone_digits(value)
    if not is_valid_mozambique_phone_digits(digits):
        raise ValidationError(
            'Introduza um contacto moçambicano válido com prefixo '
            '82, 83, 84, 85, 86 ou 87 (ex: +258 84 123 4567).'
        )
    return value.strip()


def calculate_age(birth_date, reference_date=None):
    reference_date = reference_date or date.today()
    years = reference_date.year - birth_date.year
    if (reference_date.month, reference_date.day) < (birth_date.month, birth_date.day):
        years -= 1
    return years


def validate_date_of_birth(value, *, min_age=None):
    if value is None:
        raise ValidationError('A data de nascimento é obrigatória.')

    today = date.today()
    if value > today:
        raise ValidationError('A data de nascimento não pode ser posterior à data atual.')

    if min_age is not None and calculate_age(value, today) < min_age:
        raise ValidationError(f'Deve ter pelo menos {min_age} anos.')

    return value


def user_meets_min_age(user, min_age, reference_date=None):
    if not user or not getattr(user, 'date_of_birth', None):
        return False
    return calculate_age(user.date_of_birth, reference_date) >= min_age


def can_become_seller(user, reference_date=None):
    return user_meets_min_age(user, MIN_VENDOR_AGE, reference_date)
