from django import forms
from .models import ProductReview, ReviewImage
from django.core.files.uploadedfile import UploadedFile

class ProductReviewForm(forms.ModelForm):
    class Meta:
        model = ProductReview
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(choices=ProductReview.RATING_CHOICES),
            'comment': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Chia sẻ trải nghiệm của bạn về sản phẩm...'
            }),
        }

class ReviewImageForm(forms.ModelForm):
    class Meta:
        model = ReviewImage
        fields = ['image']