# auth_app/forms.py

import logging
from django import forms
from django.core.exceptions import ValidationError
from .models import Student, Survey, Question, Choice, SurveyResponse, Answer

logger = logging.getLogger(__name__)


# --- Foydalanuvchi autentifikatsiyasi uchun forma ---

class LoginForm(forms.Form):
    """Foydalanuvchidan login va parol olish uchun standart forma."""
    username = forms.CharField(
        label="Login (ID Raqam)",
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-input', # HTMLga stil berish uchun
            'placeholder': 'Talaba ID raqamingizni kiriting'
        })
    )
    password = forms.CharField(
        label="Parol",
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Parolingiz'
        })
    )


# --- So'rovnoma uchun formalar ---

class BaseAnswerForm(forms.ModelForm):
    """
    Bitta savolga javob berish uchun asosiy forma.
    Savol turiga qarab (matnli, yagona tanlov, ko'p tanlov)
    o'z ko'rinishini va validatsiyasini o'zgartiradi.
    """
    class Meta:
        model = Answer
        fields = ['text_answer', 'selected_choice', 'selected_choices']
        # Bu maydonlar __init__ metodida dinamik ravishda sozlanadi.

    def __init__(self, *args, **kwargs):
        # Eng muhim qism: har bir formaga o'zining savolini biriktirish.
        self.question_instance = kwargs.pop('question_instance', None)
        
        super().__init__(*args, **kwargs)

        # Agar qandaydir sabab bilan savol berilmagan bo'lsa, xatolik berish.
        if not self.question_instance:
            raise ValueError("BaseAnswerForm yaratish uchun 'question_instance' berilishi shart.")

        # Yangi (saqlanmagan) Answer obyektini to'g'ri Question bilan bog'lash.
        if not self.instance.pk:
            self.instance.question = self.question_instance

        # Savol turiga qarab formalarni sozlash
        q_type = self.question_instance.question_type
        
        if q_type == 'text':
            self.fields['text_answer'].required = self.question_instance.is_required
            self.fields['text_answer'].widget.attrs.update({
                'class': 'block w-full rounded-lg border-slate-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm',
                'rows': 4,
                'placeholder': 'Javobingizni shu yerga yozing...'
            })
            # Keraksiz maydonlarni yashirish
            self.fields['selected_choice'].widget = forms.HiddenInput()
            self.fields['selected_choices'].widget = forms.HiddenInput()

        elif q_type == 'single_choice':
            self.fields['selected_choice'].queryset = self.question_instance.choices.all().order_by('pk')
            self.fields['selected_choice'].widget = forms.RadioSelect()
            self.fields['selected_choice'].empty_label = None
            self.fields['selected_choice'].label = "" # Labelni shablonda o'zimiz ko'rsatamiz
            self.fields['selected_choice'].required = self.question_instance.is_required
            # Keraksiz maydonlarni yashirish
            self.fields['text_answer'].widget = forms.HiddenInput()
            self.fields['selected_choices'].widget = forms.HiddenInput()

        elif q_type == 'multiple_choice':
            self.fields['selected_choices'].queryset = self.question_instance.choices.all().order_by('pk')
            self.fields['selected_choices'].widget = forms.CheckboxSelectMultiple()
            self.fields['selected_choices'].label = ""
            self.fields['selected_choices'].required = self.question_instance.is_required
            # Keraksiz maydonlarni yashirish
            self.fields['text_answer'].widget = forms.HiddenInput()
            self.fields['selected_choice'].widget = forms.HiddenInput()

    def clean(self):
        """Majburiy savollarga javob berilganini tekshiradi."""
        cleaned_data = super().clean()
        
        if not self.question_instance.is_required:
            return cleaned_data

        q_type = self.question_instance.question_type
        
        has_text = bool(cleaned_data.get('text_answer', '').strip())
        has_single_choice = bool(cleaned_data.get('selected_choice'))
        has_multiple_choices = bool(cleaned_data.get('selected_choices'))

        if q_type == 'text' and not has_text:
            self.add_error('text_answer', "Bu majburiy savolga javob yozilmagan.")
        elif q_type == 'single_choice' and not has_single_choice:
            self.add_error('selected_choice', "Bu majburiy savol uchun variant tanlanmagan.")
        elif q_type == 'multiple_choice' and not has_multiple_choices:
            self.add_error('selected_choices', "Bu majburiy savol uchun kamida bitta variant tanlanishi kerak.")
            
        return cleaned_data


def create_answer_form_set(survey, student=None, data=None):
    """
    Berilgan so'rovnoma uchun formset (formalar to'plami) yaratadi.
    Har bir savol uchun bittadan BaseAnswerForm yaratadi.
    """
    # So'rovnoma savollarini tartib raqami bo'yicha olish
    questions = list(survey.questions.all().order_by('order'))
    if not questions:
        logger.warning(f"So'rovnoma uchun savollar topilmadi (ID: {survey.pk})")
        return None

    # Formset yaratish uchun `formset_factory` ishlatiladi
    AnswerFormSet = forms.formset_factory(form=BaseAnswerForm, extra=0, can_delete=False)
    
    # Har bir formaga o'zining 'question_instance' sini berish uchun
    form_kwargs = [{'question_instance': q} for q in questions]

    # Agar POST so'rov bo'lsa `data` bilan, GET so'rov bo'lsa bo'sh formset yaratiladi
    if data:
        formset = AnswerFormSet(data=data, form_kwargs=form_kwargs)
    else:
        formset = AnswerFormSet(form_kwargs=form_kwargs)

    return formset