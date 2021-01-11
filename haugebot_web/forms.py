from django import forms

from .models import Setting, TwitchColor


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


class WusstestDuSchonConfigForm(forms.Form):
    prefix_field = forms.CharField(max_length=50, initial=Setting.objects.get(key="WusstestDuSchonPrefix").value,
                                   label="Präfix")
    loop_field = forms.IntegerField(initial=Setting.objects.get(key="WusstestDuSchonLoop").value,
                                    label="Pause (in Minuten)")
    color_field = forms.ChoiceField(choices=[(color.color, color.display_name) for color in TwitchColor.objects.all()],
                                    label="Text Farbe")

    def __init__(self, *args, **kwargs):
        super(WusstestDuSchonConfigForm, self).__init__(*args, **kwargs)

        self.fields["prefix_field"].initial = Setting.objects.get(key="WusstestDuSchonPrefix").value
        self.fields["loop_field"].initial = Setting.objects.get(key="WusstestDuSchonLoop").value
        self.fields["color_field"].initial = TwitchColor.objects.get(
            twitch_name=Setting.objects.get(key="WusstestDuSchonColor").value).color

        for field_name, field in self.fields.items():
            if type(field) is forms.fields.BooleanField:
                field.widget.attrs['class'] = ' w3-check '
                field.label_suffix = ""
            else:
                field.widget.attrs['class'] = ' w3-input '
            field.widget.attrs['placeholder'] = field.label

        self.fields["color_field"].widget.attrs['class'] += ' color-select '

    def save(self):
        prefix = Setting.objects.get(key="WusstestDuSchonPrefix")
        prefix.value = self.cleaned_data["prefix_field"]
        prefix.save()

        loop = Setting.objects.get(key="WusstestDuSchonLoop")
        loop.value = self.cleaned_data["loop_field"]
        loop.save()

        color = Setting.objects.get(key="WusstestDuSchonColor")
        color.value = TwitchColor.objects.get(color=self.cleaned_data["color_field"]).twitch_name
        color.save()
