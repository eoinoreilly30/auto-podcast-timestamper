from django.http import HttpResponse
from django.shortcuts import render
from django import forms
from projectsite.timestamper import main


class URLForm(forms.Form):
    url = forms.CharField(label='URL')


def urlform(request):
    if request.method == 'POST':
        form = URLForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data["url"]

            return HttpResponse('thanks')
    else:
        form = URLForm()

    return render(request, 'url-form.html', {'form': form})
