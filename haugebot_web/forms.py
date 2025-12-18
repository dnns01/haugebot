from django import forms

from .models import Setting


class BaseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(BaseForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if type(field) is forms.fields.BooleanField:
                field.widget.attrs['class'] = ' w3-check '
                field.label_suffix = ""
            else:
                field.widget.attrs['class'] = ' w3-input '
            field.widget.attrs['placeholder'] = field.label


class BaseWusstestDuSchonSettingsFormSet(forms.BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queryset = Setting.objects.filter(key__in=["WusstestDuSchonPrefix", "WusstestDuSchonLoop"])
