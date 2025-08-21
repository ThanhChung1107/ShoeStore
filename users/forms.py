from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15, required=False)
    address = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'password1', 'password2', 'address']
        
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_admin = False  # Mặc định là user thường khi đăng ký
        if commit:
            user.save()
        return user
    
class AvatarUploadForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['avatar']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['avatar'].widget.attrs.update({
            'class': 'avatar-input',
            'accept': 'image/*'
        })