from datetime import date

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

from .form_utils import apply_pt_field_errors
from .services import DELETE_CONFIRMATION_TEXT
from .validators import (
    MIN_CLIENT_AGE,
    MIN_NAME_LENGTH,
    validate_date_of_birth,
    validate_email_address,
    validate_min_name,
)
User = get_user_model()


class LoginForm(forms.Form):
    email = forms.EmailField(
        label='Email',
        error_messages={
            'required': 'O email é obrigatório.',
            'invalid': 'Introduza um endereço de email válido.',
        },
        widget=forms.EmailInput(attrs={
            'id': 'login-email',
            'placeholder': 'seu@email.com',
            'autocomplete': 'email',
        }),
    )
    password = forms.CharField(
        label='Senha',
        error_messages={
            'required': 'A senha é obrigatória.',
        },
        widget=forms.PasswordInput(attrs={
            'id': 'login-password',
            'placeholder': '••••••••',
            'autocomplete': 'current-password',
        }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_pt_field_errors(self)

    def clean_email(self):
        return validate_email_address(self.cleaned_data.get('email'))


class RegisterForm(forms.Form):
    name = forms.CharField(
        label='Nome',
        min_length=MIN_NAME_LENGTH,
        max_length=150,
        error_messages={
            'required': 'O nome é obrigatório.',
            'min_length': f'O nome deve ter pelo menos {MIN_NAME_LENGTH} caracteres.',
            'max_length': 'O nome é demasiado longo.',
        },
        widget=forms.TextInput(attrs={
            'id': 'register-name',
            'placeholder': 'O seu nome completo',
            'autocomplete': 'name',
            'minlength': MIN_NAME_LENGTH,
        }),
    )
    date_of_birth = forms.DateField(
        label='Data de nascimento',
        error_messages={
            'required': 'A data de nascimento é obrigatória.',
            'invalid': 'Introduza uma data válida.',
        },
        widget=forms.DateInput(attrs={
            'id': 'register-dob',
            'type': 'date',
        }),
    )
    gender = forms.ChoiceField(
        label='Sexo',
        choices=User.Gender.choices,
        error_messages={'required': 'O sexo é obrigatório.'},
        widget=forms.RadioSelect(attrs={
            'class': 'gender-options',
        }),
    )
    email = forms.EmailField(
        label='Email',
        error_messages={
            'required': 'O email é obrigatório.',
            'invalid': 'Introduza um endereço de email válido.',
        },
        widget=forms.EmailInput(attrs={
            'id': 'register-email',
            'placeholder': 'O seu email',
            'autocomplete': 'email',
        }),
    )
    password = forms.CharField(
        label='Senha',
        error_messages={
            'required': 'A senha é obrigatória.',
        },
        widget=forms.PasswordInput(attrs={
            'id': 'register-password',
            'placeholder': 'Crie uma senha',
            'autocomplete': 'new-password',
        }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_pt_field_errors(self)
        self.fields['date_of_birth'].widget.attrs['max'] = date.today().isoformat()

    def clean_name(self):
        return validate_min_name(self.cleaned_data.get('name'))

    def clean_date_of_birth(self):
        return validate_date_of_birth(
            self.cleaned_data.get('date_of_birth'),
            min_age=MIN_CLIENT_AGE,
        )

    def clean_gender(self):
        gender = self.cleaned_data.get('gender')
        if gender not in User.Gender.values:
            raise forms.ValidationError('Selecione um sexo válido.')
        return gender

    def clean_email(self):
        email = validate_email_address(self.cleaned_data.get('email'))
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Este email já está em uso.')
        return email

    def clean_password(self):
        password = self.cleaned_data['password']
        try:
            validate_password(password)
        except DjangoValidationError as exc:
            raise forms.ValidationError(list(exc.messages)) from exc
        return password


class AccountProfileForm(forms.Form):
    name = forms.CharField(
        label='Nome completo',
        min_length=MIN_NAME_LENGTH,
        max_length=150,
        error_messages={
            'required': 'O nome é obrigatório.',
            'min_length': f'O nome deve ter pelo menos {MIN_NAME_LENGTH} caracteres.',
            'max_length': 'O nome é demasiado longo.',
        },
        widget=forms.TextInput(attrs={
            'id': 'account-name',
            'placeholder': 'O seu nome completo',
            'autocomplete': 'name',
            'minlength': MIN_NAME_LENGTH,
        }),
    )
    date_of_birth = forms.DateField(
        label='Data de nascimento',
        error_messages={
            'required': 'A data de nascimento é obrigatória.',
            'invalid': 'Introduza uma data válida.',
        },
        widget=forms.DateInput(attrs={
            'id': 'account-dob',
            'type': 'date',
        }),
    )
    gender = forms.ChoiceField(
        label='Sexo',
        choices=User.Gender.choices,
        error_messages={'required': 'O sexo é obrigatório.'},
        widget=forms.RadioSelect(attrs={
            'class': 'gender-options',
        }),
    )
    email = forms.EmailField(
        label='Email',
        error_messages={
            'required': 'O email é obrigatório.',
            'invalid': 'Introduza um endereço de email válido.',
        },
        widget=forms.EmailInput(attrs={
            'id': 'account-email',
            'placeholder': 'O seu email',
            'autocomplete': 'email',
        }),
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        apply_pt_field_errors(self)
        self.fields['date_of_birth'].widget.attrs['max'] = date.today().isoformat()

    def clean_name(self):
        return validate_min_name(self.cleaned_data.get('name'))

    def clean_date_of_birth(self):
        return validate_date_of_birth(
            self.cleaned_data.get('date_of_birth'),
            min_age=MIN_CLIENT_AGE,
        )

    def clean_gender(self):
        gender = self.cleaned_data.get('gender')
        if gender not in User.Gender.values:
            raise forms.ValidationError('Selecione um sexo válido.')
        return gender

    def clean_email(self):
        email = validate_email_address(self.cleaned_data.get('email'))
        queryset = User.objects.filter(email__iexact=email)
        if self.user is not None:
            queryset = queryset.exclude(pk=self.user.pk)
        if queryset.exists():
            raise forms.ValidationError('Este email já está em uso.')
        return email


class AccountPasswordForm(forms.Form):
    current_password = forms.CharField(
        label='Senha actual',
        error_messages={'required': 'A senha actual é obrigatória.'},
        widget=forms.PasswordInput(attrs={
            'id': 'account-current-password',
            'placeholder': '••••••••',
            'autocomplete': 'current-password',
        }),
    )
    new_password = forms.CharField(
        label='Nova senha',
        error_messages={'required': 'A nova senha é obrigatória.'},
        widget=forms.PasswordInput(attrs={
            'id': 'account-new-password',
            'placeholder': 'Crie uma nova senha',
            'autocomplete': 'new-password',
        }),
    )
    confirm_password = forms.CharField(
        label='Confirmar nova senha',
        error_messages={'required': 'Confirme a nova senha.'},
        widget=forms.PasswordInput(attrs={
            'id': 'account-confirm-password',
            'placeholder': 'Repita a nova senha',
            'autocomplete': 'new-password',
        }),
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        apply_pt_field_errors(self)

    def clean_current_password(self):
        password = self.cleaned_data.get('current_password', '')
        if self.user is not None and not self.user.check_password(password):
            raise forms.ValidationError('A senha actual está incorrecta.')
        return password

    def clean_new_password(self):
        password = self.cleaned_data.get('new_password', '')
        try:
            validate_password(password, user=self.user)
        except DjangoValidationError as exc:
            raise forms.ValidationError(list(exc.messages)) from exc
        return password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        if new_password and confirm_password and new_password != confirm_password:
            raise forms.ValidationError('A confirmação da senha não coincide.')
        return cleaned_data


class AccountDeleteForm(forms.Form):
    password = forms.CharField(
        label='Senha',
        error_messages={'required': 'A senha é obrigatória para eliminar a conta.'},
        widget=forms.PasswordInput(attrs={
            'id': 'account-delete-password',
            'placeholder': '••••••••',
            'autocomplete': 'current-password',
        }),
    )
    confirmation = forms.CharField(
        label='Confirmar eliminação',
        error_messages={'required': 'Escreva APAGAR para confirmar a eliminação.'},
        widget=forms.TextInput(attrs={
            'id': 'account-delete-confirmation',
            'placeholder': DELETE_CONFIRMATION_TEXT,
            'autocomplete': 'off',
            'spellcheck': 'false',
        }),
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        apply_pt_field_errors(self)

    def clean_password(self):
        password = self.cleaned_data.get('password', '')
        if self.user is not None and not self.user.check_password(password):
            raise forms.ValidationError('A senha está incorrecta.')
        return password

    def clean_confirmation(self):
        value = (self.cleaned_data.get('confirmation') or '').strip().upper()
        if value != DELETE_CONFIRMATION_TEXT:
            raise forms.ValidationError(
                f'Escreva {DELETE_CONFIRMATION_TEXT} para confirmar a eliminação.'
            )
        return value


class EstablishmentReviewForm(forms.Form):
    rating = forms.ChoiceField(
        label='Avaliação',
        choices=[
            (str(value), f'{value} estrela{"s" if value > 1 else ""}')
            for value in range(5, 0, -1)
        ],
        required=False,
        widget=forms.RadioSelect(attrs={'class': 'review-rating-input'}),
    )
    comment = forms.CharField(
        label='Comentário',
        max_length=1000,
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': 'Partilhe a sua experiência com este estabelecimento...',
            'class': 'review-comment-input',
        }),
        error_messages={
            'max_length': 'O comentário não pode exceder 1000 caracteres.',
        },
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_pt_field_errors(self)

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if not rating:
            return None
        return int(rating)

    def clean_comment(self):
        return (self.cleaned_data.get('comment') or '').strip()

    def clean(self):
        cleaned_data = super().clean()
        rating = cleaned_data.get('rating')
        comment = cleaned_data.get('comment', '')
        if rating is None and not comment:
            raise forms.ValidationError(
                'Indique uma avaliação, escreva um comentário ou envie ambos.'
            )
        return cleaned_data
