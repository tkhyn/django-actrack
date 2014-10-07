import django

if django.VERSION < (1, 6):
    xa0space = u' '
else:
    xa0space = u'\xa0'
