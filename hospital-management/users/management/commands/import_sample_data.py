"""
Management command: import_sample_data
=======================================
Parses the medical_db_best_practice.sql file and imports its data
into your existing Django models — no schema changes required.

Usage:
    python manage.py import_sample_data
    python manage.py import_sample_data --sql path/to/other.sql
    python manage.py import_sample_data --clear   # wipe existing sample data first

What gets imported:
    - Specialty      (from distinct specialite values in medecin table)
    - Users          (one PARENT user per unique parent family + one DOCTOR user per medecin)
    - Doctors        (linked to their Users)
    - Patients       (linked to their parent Users)
    - Allergie       (linked to Patients)
    - Antecedent     (linked to Patients)
    - Appointment    (from rendez_vous, linked to Doctor + Patient)
    - Consultation   (from consultation, linked to Appointment)
    - Diagnostic     (linked to Consultation)
    - Traitement     (linked to Consultation)
"""

import re
import os
from datetime import datetime, date

from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.hashers import make_password

from users.models import Users, Specialty, Doctors, Patients
from medical_history.models import Allergie, Antecedent
from consultations.models import Appointment, Consultation, Diagnostic, Traitement


# ── helpers ───────────────────────────────────────────────────────────────────

def _parse_inserts(sql_text, table):
    """
    Extract all INSERT rows for a given table name.
    Returns a list of tuples, one per INSERT row.
    Handles multi-value inserts and single-value inserts.
    """
    # Match:  INSERT INTO <table> (...) VALUES (...);
    pattern = re.compile(
        rf"INSERT INTO {table}\s*\([^)]+\)\s*VALUES\s*(\(.*?\));",
        re.IGNORECASE | re.DOTALL,
    )
    rows = []
    for m in pattern.finditer(sql_text):
        values_str = m.group(1)
        rows.append(_parse_values(values_str))
    return rows


def _parse_values(values_str):
    """
    Parse a single SQL VALUES tuple like:
        ('uuid', 'John', NULL, '2020-01-01')
    into a Python tuple of strings/None.
    Handles escaped single quotes ('').
    """
    # Strip outer parens
    inner = values_str.strip()
    if inner.startswith('('):
        inner = inner[1:]
    if inner.endswith(')'):
        inner = inner[:-1]

    result = []
    current = ''
    in_string = False
    i = 0
    while i < len(inner):
        c = inner[i]
        if c == "'" and not in_string:
            in_string = True
            i += 1
            continue
        if c == "'" and in_string:
            # escaped quote?
            if i + 1 < len(inner) and inner[i + 1] == "'":
                current += "'"
                i += 2
                continue
            else:
                in_string = False
                i += 1
                continue
        if c == ',' and not in_string:
            val = current.strip()
            result.append(None if val.upper() == 'NULL' else val)
            current = ''
            i += 1
            continue
        current += c
        i += 1

    val = current.strip()
    result.append(None if val.upper() == 'NULL' else val)
    return tuple(result)


def _d(value):
    """Convert a string date to a Python date, or None."""
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return None


# ── gravite mapping SQL → Django ──────────────────────────────────────────────
GRAVITE_MAP = {
    'faible':   'LEGERE',
    'modérée':  'MODEREE',
    'élevée':   'SEVERE',
    'critique': 'CRITIQUE',
}

TYPE_MALADIE_MAP = {
    'aiguë':     'AIGU',
    'chronique': 'CHRONIQUE',
}

REACTION_MAP = {
    'faible':   'LEGERE',
    'modérée':  'MODEREE',
    'élevée':   'SEVERE',
    'critique': 'CRITIQUE',
}

STATUS_MAP = {
    'planifié':  'PENDING',
    'confirmé':  'CONFIRMED',
    'effectué':  'COMPLETED',
    'annulé':    'CANCELLED',
}


# ── command ───────────────────────────────────────────────────────────────────

class Command(BaseCommand):
    help = 'Import sample medical data from SQL file into Django models'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sql',
            default=os.path.join(
                os.path.dirname(__file__),
                '..', '..', '..', 'data', 'medical_db_best_practice.sql'
            ),
            help='Path to the SQL file (default: data/medical_db_best_practice.sql)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing imported sample data before importing',
        )

    def handle(self, *args, **options):
        sql_path = os.path.abspath(options['sql'])

        if not os.path.exists(sql_path):
            self.stderr.write(self.style.ERROR(f'SQL file not found: {sql_path}'))
            self.stderr.write('Pass the correct path with --sql /path/to/file.sql')
            return

        self.stdout.write(f'Reading SQL file: {sql_path}')
        with open(sql_path, 'r', encoding='utf-8') as f:
            sql = f.read()

        if options['clear']:
            self._clear_data()

        with transaction.atomic():
            uuid_to_patient  = {}   # sql UUID str → Patients instance
            uuid_to_doctor   = {}   # sql UUID str → Doctors instance
            uuid_to_consult  = {}   # sql UUID str → Consultation instance

            self._import_specialties(sql)
            self._import_doctors(sql, uuid_to_doctor)
            self._import_patients_and_parents(sql, uuid_to_patient)
            self._import_allergies(sql, uuid_to_patient)
            self._import_antecedents(sql, uuid_to_patient)
            self._import_appointments_and_consultations(
                sql, uuid_to_patient, uuid_to_doctor, uuid_to_consult
            )

        self.stdout.write(self.style.SUCCESS('✓ Sample data imported successfully.'))

    # ── clear ─────────────────────────────────────────────────────────────────

    def _clear_data(self):
        self.stdout.write('Clearing existing sample data...')
        Traitement.objects.all().delete()
        Diagnostic.objects.all().delete()
        Consultation.objects.all().delete()
        Appointment.objects.all().delete()
        Antecedent.objects.all().delete()
        Allergie.objects.all().delete()
        Patients.objects.all().delete()
        Doctors.objects.all().delete()
        Users.objects.filter(role__in=['DOCTOR', 'PARENT']).delete()
        Specialty.objects.all().delete()
        self.stdout.write('  Cleared.')

    # ── specialties ───────────────────────────────────────────────────────────

    def _import_specialties(self, sql):
        rows = _parse_inserts(sql, 'medecin')
        # columns: id, nom, prenom, specialite, telephone, email
        seen = set()
        created = 0
        for row in rows:
            if len(row) < 4:
                continue
            spec_name = row[3]
            if spec_name and spec_name not in seen:
                seen.add(spec_name)
                _, made = Specialty.objects.get_or_create(name=spec_name)
                if made:
                    created += 1
        self.stdout.write(f'  Specialties: {created} created ({len(seen)} total)')

    # ── doctors ───────────────────────────────────────────────────────────────

    def _import_doctors(self, sql, uuid_to_doctor):
        rows = _parse_inserts(sql, 'medecin')
        # columns: id, nom, prenom, specialite, telephone, email
        created = 0
        skipped = 0
        for row in rows:
            if len(row) < 6:
                continue
            sql_id, nom, prenom, specialite, telephone, email = row[:6]

            if not email:
                skipped += 1
                continue

            # username from email prefix, made unique
            username_base = email.split('@')[0][:140]
            username = username_base
            suffix = 1
            while Users.objects.filter(username=username).exists():
                username = f'{username_base}_{suffix}'
                suffix += 1

            user, made = Users.objects.get_or_create(
                email=email,
                defaults={
                    'username':   username,
                    'first_name': prenom or '',
                    'last_name':  nom or '',
                    'role':       'DOCTOR',
                    'phone':      telephone or '',
                    'password':   make_password('Doctor@1234'),
                    'is_active':  True,
                }
            )

            specialty = Specialty.objects.filter(name=specialite).first()
            if not specialty:
                specialty, _ = Specialty.objects.get_or_create(name=specialite or 'GENERAL PRACTICE')

            doctor, doc_made = Doctors.objects.get_or_create(
                user=user,
                defaults={'specialty': specialty, 'bio': ''}
            )
            uuid_to_doctor[sql_id] = doctor
            if made:
                created += 1
            else:
                skipped += 1

        self.stdout.write(f'  Doctors: {created} created, {skipped} skipped (duplicate email)')

    # ── patients & parents ────────────────────────────────────────────────────

    def _import_patients_and_parents(self, sql, uuid_to_patient):
        patient_rows = _parse_inserts(sql, 'patient')
        parent_rows  = _parse_inserts(sql, 'parent')

        # Build map: patient_uuid → first père parent row
        # columns: id, nom, prenom, telephone, adresse, relation, id_patient
        patient_to_parent = {}
        for row in parent_rows:
            if len(row) < 7:
                continue
            _id, nom, prenom, telephone, adresse, relation, id_patient = row[:7]
            if id_patient not in patient_to_parent:
                # prefer père, fallback to first available
                if relation == 'père' or id_patient not in patient_to_parent:
                    patient_to_parent[id_patient] = {
                        'nom': nom, 'prenom': prenom,
                        'telephone': telephone, 'adresse': adresse,
                        'relation': relation,
                    }

        # Cache parent Users by (nom, prenom) to avoid duplicates
        parent_user_cache = {}
        patients_created = 0
        parents_created  = 0

        for row in patient_rows:
            # columns: id, nom, prenom, date_naissance, sexe,
            #          adresse, ville, etat, date_creation_dossier
            if len(row) < 5:
                continue
            sql_id   = row[0]
            nom      = row[1] or ''
            prenom   = row[2] or ''
            dob      = _d(row[3])
            sexe     = row[4] or ''

            # ── find or create parent user ────────────────────────────────────
            p_info = patient_to_parent.get(sql_id)
            if p_info:
                p_nom    = p_info['nom']    or nom
                p_prenom = p_info['prenom'] or 'Parent'
                p_tel    = p_info['telephone'] or ''
            else:
                p_nom    = nom
                p_prenom = 'Parent'
                p_tel    = ''

            cache_key = (p_nom, p_prenom)
            if cache_key in parent_user_cache:
                parent_user = parent_user_cache[cache_key]
            else:
                # Build a unique username + email
                username_base = f"{p_prenom.lower()}.{p_nom.lower()}"
                username_base = re.sub(r'[^a-z0-9._]', '', username_base)[:100] or 'parent'
                username = username_base
                suffix = 1
                while Users.objects.filter(username=username).exists():
                    username = f'{username_base}_{suffix}'
                    suffix += 1

                email_base = f"{username}@hospital.dz"
                email = email_base
                e_suffix = 1
                while Users.objects.filter(email=email).exists():
                    email = f"{username}_{e_suffix}@hospital.dz"
                    e_suffix += 1

                parent_user = Users.objects.create(
                    username=username,
                    email=email,
                    first_name=p_prenom,
                    last_name=p_nom,
                    role='PARENT',
                    phone=p_tel,
                    password=make_password('Parent@1234'),
                    is_active=True,
                )
                parent_user_cache[cache_key] = parent_user
                parents_created += 1

            # ── create patient ────────────────────────────────────────────────
            patient = Patients.objects.create(
                parent=parent_user,
                first_name=prenom,
                last_name=nom,
                birth_date=dob,
                gender=sexe if sexe in ('M', 'F') else '',
            )
            uuid_to_patient[sql_id] = patient
            patients_created += 1

        self.stdout.write(f'  Parents:  {parents_created} created')
        self.stdout.write(f'  Patients: {patients_created} created')

    # ── allergies ─────────────────────────────────────────────────────────────

    def _import_allergies(self, sql, uuid_to_patient):
        rows = _parse_inserts(sql, 'allergie')
        # columns: id, allergene, reaction, date_detection, id_patient
        created = skipped = 0
        for row in rows:
            if len(row) < 5:
                continue
            _id, allergene, reaction, date_detection, id_patient = row[:5]

            patient = uuid_to_patient.get(id_patient)
            if not patient:
                skipped += 1
                continue

            # Map reaction text → gravite choice
            # The SQL reaction column is free text, not an enum
            # We default to LEGERE and keep the text in description
            Allergie.objects.create(
                patient=patient,
                nom=allergene or 'Inconnue',
                reaction='LEGERE',
                description=reaction or '',
                date_detection=_d(date_detection),
            )
            created += 1

        self.stdout.write(f'  Allergies: {created} created, {skipped} skipped (unknown patient)')

    # ── antécédents ───────────────────────────────────────────────────────────

    def _import_antecedents(self, sql, uuid_to_patient):
        rows = _parse_inserts(sql, 'antecedent')
        # columns: id, description, type, date_declaration, id_patient
        created = skipped = 0
        for row in rows:
            if len(row) < 5:
                continue
            _id, description, type_ant, date_declaration, id_patient = row[:5]

            patient = uuid_to_patient.get(id_patient)
            if not patient:
                skipped += 1
                continue

            # Map SQL enum → Django choices
            type_map = {
                'médical':      'MEDICAL',
                'chirurgical':  'CHIRURGICAL',
                'familial':     'FAMILIAL',
                'autre':        'AUTRE',
            }
            type_val = type_map.get(type_ant, 'MEDICAL')

            Antecedent.objects.create(
                patient=patient,
                description=description or '',
                type_antecedent=type_val,
                date_declaration=_d(date_declaration),
            )
            created += 1

        self.stdout.write(f'  Antécédents: {created} created, {skipped} skipped (unknown patient)')

    # ── appointments + consultations + diagnostics + traitements ─────────────

    def _import_appointments_and_consultations(
        self, sql, uuid_to_patient, uuid_to_doctor, uuid_to_consult
    ):
        # ── rendez_vous → Appointment ─────────────────────────────────────────
        rdv_rows = _parse_inserts(sql, 'rendez_vous')
        # columns: id, date, heure, statut, id_patient, id_medecin
        rdv_map = {}   # sql rdv uuid → Appointment
        appt_created = appt_skipped = 0

        # We need an admin user as created_by
        admin_user = Users.objects.filter(role='ADMIN').first()

        for row in rdv_rows:
            if len(row) < 6:
                continue
            sql_id, date_str, heure, statut, id_patient, id_medecin = row[:6]

            patient = uuid_to_patient.get(id_patient)
            doctor  = uuid_to_doctor.get(id_medecin)
            if not patient or not doctor:
                appt_skipped += 1
                continue

            date_rdv_str = f"{date_str} {heure or '09:00:00'}"
            try:
                date_rdv = datetime.strptime(date_rdv_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    date_rdv = datetime.strptime(date_rdv_str, '%Y-%m-%d %H:%M')
                except ValueError:
                    appt_skipped += 1
                    continue

            status = STATUS_MAP.get(statut, 'PENDING')

            appt = Appointment.objects.create(
                doctor=doctor,
                patient=patient,
                date_rdv=date_rdv,
                reason='Importé depuis données échantillon',
                status=status,
                created_by=admin_user,
            )
            rdv_map[sql_id] = appt
            appt_created += 1

        self.stdout.write(f'  Appointments: {appt_created} created, {appt_skipped} skipped')

        # ── consultation → Consultation ───────────────────────────────────────
        # SQL columns: id, date, motif, poids, taille, observations, id_patient, id_medecin
        consult_rows = _parse_inserts(sql, 'consultation')
        consult_created = consult_skipped = 0

        for row in consult_rows:
            if len(row) < 8:
                continue
            sql_id, date_str, motif, poids, taille, observations, id_patient, id_medecin = row[:8]

            patient = uuid_to_patient.get(id_patient)
            doctor  = uuid_to_doctor.get(id_medecin)
            if not patient or not doctor:
                consult_skipped += 1
                continue

            # Find a COMPLETED appointment for this patient+doctor,
            # or create a dedicated one
            appt = Appointment.objects.filter(
                patient=patient,
                doctor=doctor,
                status='COMPLETED',
            ).exclude(
                consultation__isnull=False   # not already used
            ).first()

            if not appt:
                try:
                    appt_date = datetime.strptime(date_str, '%Y-%m-%d')
                except (ValueError, TypeError):
                    appt_date = datetime.now()

                appt = Appointment.objects.create(
                    doctor=doctor,
                    patient=patient,
                    date_rdv=appt_date,
                    reason=motif or 'Consultation importée',
                    status='COMPLETED',
                    created_by=admin_user,
                )

            try:
                poids_val  = float(poids)  if poids  else 20.0
                taille_val = float(taille) if taille else 100.0
            except ValueError:
                poids_val, taille_val = 20.0, 100.0

            consult = Consultation.objects.create(
                appointment=appt,
                poids=poids_val,
                taille=taille_val,
                temperature=37.0,
                observation=observations or motif or '',
            )
            uuid_to_consult[sql_id] = consult
            consult_created += 1

        self.stdout.write(f'  Consultations: {consult_created} created, {consult_skipped} skipped')

        # ── diagnostic ────────────────────────────────────────────────────────
        diag_rows = _parse_inserts(sql, 'diagnostic')
        # columns: id, nom_maladie, type_maladie, gravite, commentaire, id_consultation
        diag_created = diag_skipped = 0

        for row in diag_rows:
            if len(row) < 6:
                continue
            sql_id, nom_maladie, type_maladie, gravite, commentaire, id_consult = row[:6]

            consult = uuid_to_consult.get(id_consult)
            if not consult:
                diag_skipped += 1
                continue

            Diagnostic.objects.create(
                consultation=consult,
                nom_maladie=nom_maladie or 'Non précisé',
                type_maladie=TYPE_MALADIE_MAP.get(type_maladie, 'AUTRE'),
                gravite=GRAVITE_MAP.get(gravite, 'LEGERE'),
                commentaire_medical=commentaire or '',
                explication_parent='',
            )
            diag_created += 1

        self.stdout.write(f'  Diagnostics: {diag_created} created, {diag_skipped} skipped')

        # ── traitement ────────────────────────────────────────────────────────
        trait_rows = _parse_inserts(sql, 'traitement')
        # columns: id, medicament, dose, duree, instructions, id_consultation
        trait_created = trait_skipped = 0

        for row in trait_rows:
            if len(row) < 6:
                continue
            sql_id, medicament, dose, duree, instructions, id_consult = row[:6]

            consult = uuid_to_consult.get(id_consult)
            if not consult:
                trait_skipped += 1
                continue

            Traitement.objects.create(
                consultation=consult,
                medicament=medicament or 'Non précisé',
                dose=dose or '',
                duree=duree or '',
                instructions=instructions or '',
            )
            trait_created += 1

        self.stdout.write(f'  Traitements: {trait_created} created, {trait_skipped} skipped')