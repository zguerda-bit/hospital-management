from django import forms
from .models import Appointment, Consultation, Diagnostic, Traitement
from users.models import Doctors, Patients


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['patient', 'doctor', 'date_rdv', 'reason']
        widgets = {
            'date_rdv': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'reason': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'patient': 'Patient',
            'doctor': 'Médecin',
            'date_rdv': 'Date et heure',
            'reason': 'Motif de consultation',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date_rdv'].input_formats = ['%Y-%m-%dT%H:%M']


class ConsultationForm(forms.ModelForm):
    class Meta:
        model = Consultation
        fields = ['poids', 'taille', 'temperature', 'observation']
        labels = {
            'poids': 'Poids (kg)',
            'taille': 'Taille (cm)',
            'temperature': 'Température (°C)',
            'observation': 'Observations cliniques',
        }
        widgets = {
            'observation': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_poids(self):
        val = self.cleaned_data.get('poids')
        if val is not None and (val <= 0 or val > 300):
            raise forms.ValidationError("Poids invalide (doit être entre 0 et 300 kg).")
        return val

    def clean_taille(self):
        val = self.cleaned_data.get('taille')
        if val is not None and (val <= 0 or val > 250):
            raise forms.ValidationError("Taille invalide (doit être entre 0 et 250 cm).")
        return val

    def clean_temperature(self):
        val = self.cleaned_data.get('temperature')
        if val is not None and (val < 30 or val > 45):
            raise forms.ValidationError("Température invalide (doit être entre 30 et 45 °C).")
        return val


class DiagnosticForm(forms.ModelForm):
    class Meta:
        model = Diagnostic
        fields = ['nom_maladie', 'type_maladie', 'gravite', 'commentaire_medical', 'explication_parent']
        labels = {
            'nom_maladie': 'Nom de la maladie',
            'type_maladie': 'Type',
            'gravite': 'Gravité',
            'commentaire_medical': 'Commentaire médical',
            'explication_parent': 'Explication pour les parents',
        }
        widgets = {
            'commentaire_medical': forms.Textarea(attrs={'rows': 3}),
            'explication_parent': forms.Textarea(attrs={'rows': 3}),
        }


class TraitementForm(forms.ModelForm):
    class Meta:
        model = Traitement
        fields = ['medicament', 'dose', 'duree', 'instructions']
        labels = {
            'medicament': 'Médicament',
            'dose': 'Dose',
            'duree': 'Durée',
            'instructions': 'Instructions',
        }
        widgets = {
            'instructions': forms.Textarea(attrs={'rows': 3}),
        }