from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect, render
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.main.forms import AccountDeleteForm, AccountPasswordForm, AccountProfileForm
from apps.main.jwt_utils import REFRESH_COOKIE, clear_jwt_cookies, get_tokens_for_user, set_jwt_cookies
from apps.main.profile import Profile, set_active_profile
from apps.main.services import delete_user_account, get_self_account_deletion_block_reason
from apps.vendor.decorators import login_required_view


def _profile_form_initial(user):
    return {
        'name': user.name,
        'email': user.email,
        'date_of_birth': user.date_of_birth,
        'gender': user.gender,
    }


@login_required_view
def account_settings(request):
    profile_form = AccountProfileForm(
        initial=_profile_form_initial(request.user),
        user=request.user,
    )
    password_form = AccountPasswordForm(user=request.user)
    delete_form = AccountDeleteForm(user=request.user)
    delete_block_reason = get_self_account_deletion_block_reason(request.user)

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'profile':
            profile_form = AccountProfileForm(
                request.POST,
                user=request.user,
            )
            if profile_form.is_valid():
                user = request.user
                user.name = profile_form.cleaned_data['name']
                user.email = profile_form.cleaned_data['email']
                user.date_of_birth = profile_form.cleaned_data['date_of_birth']
                user.gender = profile_form.cleaned_data['gender']
                user.save()
                messages.success(
                    request,
                    'Os seus dados foram actualizados com sucesso.',
                    extra_tags='account',
                )
                return redirect('account_settings')
        elif form_type == 'password':
            password_form = AccountPasswordForm(
                request.POST,
                user=request.user,
            )
            if password_form.is_valid():
                user = request.user
                user.set_password(password_form.cleaned_data['new_password'])
                user.save()
                tokens = get_tokens_for_user(user)
                messages.success(
                    request,
                    'A sua senha foi alterada com sucesso.',
                    extra_tags='account',
                )
                response = redirect('account_settings')
                return set_jwt_cookies(response, tokens)
        elif form_type == 'delete':
            delete_form = AccountDeleteForm(
                request.POST,
                user=request.user,
            )
            if delete_block_reason:
                messages.error(request, delete_block_reason, extra_tags='account')
                return redirect('account_settings')
            if delete_form.is_valid():
                user = request.user
                refresh_token = request.COOKIES.get(REFRESH_COOKIE)
                if refresh_token:
                    try:
                        RefreshToken(refresh_token).blacklist()
                    except TokenError:
                        pass
                logout(request)
                delete_user_account(user)
                messages.success(
                    request,
                    'A sua conta foi eliminada definitivamente.',
                    extra_tags='general',
                )
                response = redirect('auth')
                return clear_jwt_cookies(response)

    return render(request, 'main/account_settings.html', {
        'profile_form': profile_form,
        'password_form': password_form,
        'delete_form': delete_form,
        'delete_block_reason': delete_block_reason,
        'user_roles': request.user.get_roles_display(),
    })


def switch_profile(request):
    if not request.user.is_authenticated:
        return redirect('auth')

    profile = request.GET.get('profile', Profile.CLIENTE)

    if profile == Profile.VENDEDOR:
        if not request.user.is_vendedor:
            messages.info(request, 'Precisa de ser vendedor para aceder a esse perfil.', extra_tags='vendor')
            return redirect('vendor:become_seller')
        set_active_profile(request, Profile.VENDEDOR)
        return redirect('vendor:dashboard')

    set_active_profile(request, Profile.CLIENTE)
    messages.success(request, 'Perfil alterado para Cliente.', extra_tags='profile')
    return redirect('home')
