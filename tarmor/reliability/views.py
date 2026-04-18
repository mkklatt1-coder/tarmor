from django.shortcuts import render


def reliability(request):
    return render(request, 'reliability/reliability.html')
