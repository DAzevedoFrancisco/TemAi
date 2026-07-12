from django import forms

from apps.main.form_utils import apply_pt_field_errors
from apps.main.validators import validate_email_address


class PromoteAdminForm(forms.Form):
    email = forms.EmailField(
        label='Email do utilizador',
        error_messages={
            'required': 'O email é obrigatório.',
            'invalid': 'Introduza um endereço de email válido.',
        },
        widget=forms.EmailInput(attrs={
            'placeholder': 'utilizador@email.com',
            'autocomplete': 'email',
        }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_pt_field_errors(self)

    def clean_email(self):
        return validate_email_address(self.cleaned_data.get('email'))
