from django import forms
from .models import Brand, Tag

class CosmeSearchForm(forms.Form):
    product_name = forms.CharField(label='商品名', required=False, max_length=100)
    brand = forms.ModelChoiceField(label='ブランド', queryset=Brand.objects.all(), required=False)
    tag = forms.ModelChoiceField(label='タグ', queryset=Tag.objects.all(), required=False)
    ingredient = forms.CharField(label='成分', required=False, max_length=255)
    

class TestMailForm(forms.Form):
    email = forms.EmailField(label="テスト送信先メールアドレス")

