from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from allauth.account.forms import ChangePasswordForm
from allauth.account.internal.flows.password_change import finalize_password_change
from .forms import UserProfileForm

@login_required
def settings_profile(request):
    if request.headers.get('HX-Request'):
        return render(request, 'settings/partials/profile_detail.html')
    return render(request, 'settings/profile.html')


@login_required
def settings_profile_edit(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tu perfil se ha actualizado correctamente.')
            if request.headers.get('HX-Request') == 'true':
                return render(request, 'settings/partials/profile_detail.html', {'form': form})
        else:
            messages.error(request, 'Por favor, corrige los errores abajo.')
            if request.headers.get('HX-Request') == 'true':
                return render(request, 'settings/partials/profile_form.html', {'form': form})
    else:
        form = UserProfileForm(instance=request.user)
        
    return render(request, 'settings/profile_edit.html', {'form': form})


@login_required
def settings_password_change(request):
    if not request.user.has_usable_password():
        return redirect('account_set_password')

    if request.method == 'POST':
        form = ChangePasswordForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            finalize_password_change(request, request.user)
            if request.headers.get('HX-Request') == 'true':
                context = {'form': form}
                return render(request, 'settings/partials/profile_detail.html', context)
        else:
            messages.error(request, 'Por favor, corrige los errores abajo.')
            if request.headers.get('HX-Request') == 'true':
                return render(request, 'settings/password_change.html', {'form': form})
    else:
        form = ChangePasswordForm(user=request.user)

    return render(request, 'settings/password_change.html', {'form': form})

        
