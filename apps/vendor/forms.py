from django import forms

from apps.main.form_utils import apply_pt_field_errors
from apps.main.validators import MIN_NAME_LENGTH, title_case_name, validate_min_name, validate_mozambique_phone

from .geo import is_within_beira
from .models import Category, Establishment, Product


class EstablishmentForm(forms.ModelForm):
    latitude = forms.DecimalField(
        widget=forms.HiddenInput(),
        required=True,
        error_messages={
            'required': 'Selecione a localização no mapa.',
            'invalid': 'Coordenada de latitude inválida.',
        },
    )
    longitude = forms.DecimalField(
        widget=forms.HiddenInput(),
        required=True,
        error_messages={
            'required': 'Selecione a localização no mapa.',
            'invalid': 'Coordenada de longitude inválida.',
        },
    )
    user_latitude = forms.DecimalField(
        widget=forms.HiddenInput(),
        required=False,
        error_messages={'invalid': 'Coordenada de latitude do utilizador inválida.'},
    )
    user_longitude = forms.DecimalField(
        widget=forms.HiddenInput(),
        required=False,
        error_messages={'invalid': 'Coordenada de longitude do utilizador inválida.'},
    )

    class Meta:
        model = Establishment
        fields = ['name', 'address', 'phone', 'opening_hours', 'latitude', 'longitude']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Ex: Mercado Central', 'class': 'form-control'}),
            'address': forms.Textarea(attrs={'placeholder': 'Rua, bairro, número — Beira', 'rows': 3, 'class': 'form-control'}),
            'phone': forms.TextInput(attrs={
                'placeholder': '+258 84 000 0000',
                'class': 'form-control',
                'inputmode': 'tel',
                'autocomplete': 'tel',
            }),
            'opening_hours': forms.TextInput(attrs={
                'placeholder': 'Ex: Seg-Sex 09:00-18:00, Sáb 09:00-13:00',
                'class': 'form-control',
            }),
        }
        labels = {
            'name': 'Nome',
            'address': 'Endereço',
            'phone': 'Telefone',
            'opening_hours': 'Horário de funcionamento',
        }
        error_messages = {
            'name': {
                'required': 'O nome do estabelecimento é obrigatório.',
                'min_length': f'O nome deve ter pelo menos {MIN_NAME_LENGTH} caracteres.',
                'max_length': 'O nome é demasiado longo.',
            },
            'address': {
                'required': 'O endereço é obrigatório.',
            },
            'phone': {
                'required': 'O telefone é obrigatório.',
                'max_length': 'O telefone é demasiado longo.',
                'invalid': 'Introduza um contacto moçambicano válido com prefixo 82, 83, 84, 85, 86 ou 87.',
            },
            'opening_hours': {
                'required': 'O horário de funcionamento é obrigatório.',
                'max_length': 'O horário é demasiado longo.',
            },
        }

    def __init__(self, *args, require_user_location=False, **kwargs):
        self.require_user_location = require_user_location
        super().__init__(*args, **kwargs)
        self.fields['name'].min_length = MIN_NAME_LENGTH
        self.fields['name'].widget.attrs.setdefault('minlength', MIN_NAME_LENGTH)
        apply_pt_field_errors(self)

    def clean_name(self):
        return validate_min_name(
            self.cleaned_data.get('name'),
            field_label='O nome do estabelecimento',
        )

    def clean_phone(self):
        return validate_mozambique_phone(self.cleaned_data.get('phone'))

    def clean(self):
        cleaned_data = super().clean()
        latitude = cleaned_data.get('latitude')
        longitude = cleaned_data.get('longitude')

        if latitude is not None and longitude is not None:
            if not is_within_beira(latitude, longitude):
                raise forms.ValidationError(
                    'A localização do estabelecimento deve estar dentro da cidade da Beira, Sofala, Moçambique.'
                )

        if self.require_user_location:
            user_lat = cleaned_data.get('user_latitude')
            user_lng = cleaned_data.get('user_longitude')
            if user_lat is None or user_lng is None:
                raise forms.ValidationError(
                    'É obrigatório autorizar a localização GPS para cadastrar um estabelecimento.'
                )
            if not is_within_beira(user_lat, user_lng):
                raise forms.ValidationError(
                    'A sua localização está fora da cidade da Beira. '
                    'Só pode cadastrar estabelecimentos estando na Beira.'
                )

        return cleaned_data


class ProductForm(forms.ModelForm):
    is_available = forms.BooleanField(
        label='Disponível para clientes',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'availability-checkbox-input'}),
    )

    class Meta:
        model = Product
        fields = ['name', 'description', 'image', 'category', 'is_available']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Nome do produto', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'placeholder': 'Descreva o produto...', 'rows': 4, 'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control-file', 'accept': 'image/*'}),
        }
        labels = {
            'name': 'Nome',
            'description': 'Descrição',
            'image': 'Imagem',
            'category': 'Categoria',
        }
        error_messages = {
            'name': {
                'required': 'O nome do produto é obrigatório.',
                'max_length': 'O nome é demasiado longo.',
            },
            'category': {
                'required': 'Selecione uma categoria.',
                'invalid_choice': 'Selecione uma categoria válida.',
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        self.fields['category'].empty_label = 'Selecione uma categoria'
        if not self.instance.pk:
            self.fields['is_available'].initial = True
        apply_pt_field_errors(self)

    def clean_name(self):
        return title_case_name(self.cleaned_data.get('name'))

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            return image
        if self.instance.pk and self.instance.image:
            return self.instance.image
        raise forms.ValidationError('A imagem é obrigatória.')
