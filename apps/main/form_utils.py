COMMON_FIELD_ERRORS = {
    'required': 'Este campo é obrigatório.',
    'invalid': 'Introduza um valor válido.',
    'invalid_email': 'Introduza um endereço de email válido.',
    'max_length': 'Este valor é demasiado longo.',
    'min_length': 'Este valor é demasiado curto.',
    'max_value': 'Este valor é demasiado alto.',
    'min_value': 'Este valor é demasiado baixo.',
    'max_digits': 'Demasiados dígitos.',
    'max_decimal_places': 'Demasiadas casas decimais.',
    'max_whole_digits': 'Demasiados dígitos antes da vírgula.',
}


def apply_pt_field_errors(form):
    for field in form.fields.values():
        for key, message in COMMON_FIELD_ERRORS.items():
            field.error_messages.setdefault(key, message)
