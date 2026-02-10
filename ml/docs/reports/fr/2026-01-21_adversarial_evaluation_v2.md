# Évaluation Adversariale - NER Légal Espagnol

**Date :** 2026-01-21
**Modèle :** legal_ner_v2
**Tests :** 35

---

## Résumé Exécutif

| Métrique | Valeur |
|-----|-----|
| Tests Totaux | 35 |
| Réussis | 19 (54.3%) |
| Échoués | 16 (45.7%) |

### Par Catégorie

| Catégorie | Réussis | Total | Taux |
|-----|-----|-----|-----|
| adversarial | 5 | 8 | 62.5% |
| edge_case | 6 | 9 | 66.7% |
| ocr_corruption | 2 | 5 | 40.0% |
| real_world | 5 | 10 | 50.0% |
| unicode_evasion | 1 | 3 | 33.3% |

### Par Difficulté

| Difficulté | Réussis | Total | Taux |
|-----|-----|-----|-----|
| easy | 4 | 4 | 100.0% |
| medium | 9 | 12 | 75.0% |
| hard | 6 | 19 | 31.6% |

---

## Résultats Détaillés

### CAS LIMITE (EDGE CASE)

#### single_letter_name [PASS]

**Difficulté :** medium

**Texte :**
```
El demandante J. García presentó recurso.
```

**Attendu (1) :**
- `J. García` → PERSON

**Détecté (1) :**
- `J. García` → PERSON

**Résultat :** 1 corrects, 0 manqués, 0 faux positifs

**Notes :** Motif initiale + nom de famille

---

#### very_long_name [PASS]

**Difficulté :** hard

**Texte :**
```
Compareció Don José María de la Santísima Trinidad Fernández-López de Haro y Martínez de Pisón.
```

**Attendu (1) :**
- `José María de la Santísima Trinidad Fernández-López de Haro y Martínez de Pisón` → PERSON

**Détecté (1) :**
- `Don José María de la Santísima Trinidad Fernández-López de Haro y Martínez de Pisón` → PERSON

**Résultat :** 1 corrects, 0 manqués, 0 faux positifs

**Notes :** Nom noble composé avec particules

---

#### dni_without_letter [PASS]

**Difficulté :** medium

**Texte :**
```
DNI número 12345678 (pendiente de verificación).
```

**Attendu (1) :**
- `12345678` → DNI_NIE

**Détecté (1) :**
- `12345678` → DNI_NIE

**Résultat :** 1 corrects, 0 manqués, 0 faux positifs

**Notes :** DNI sans lettre de contrôle

---

#### dni_with_spaces [FAIL]

**Difficulté :** hard

**Texte :**
```
Su documento de identidad es 12 345 678 Z.
```

**Attendu (1) :**
- `12 345 678 Z` → DNI_NIE

**Détecté (3) :**
- `12` → DNI_NIE
- `3` → NSS
- `45 678 Z` → DNI_NIE

**Résultat :** 1 corrects, 0 manqués, 2 faux positifs

**Notes :** DNI avec espaces internes

---

#### iban_with_spaces [PASS]

**Difficulté :** easy

**Texte :**
```
Transferir a ES91 2100 0418 4502 0005 1332.
```

**Attendu (1) :**
- `ES91 2100 0418 4502 0005 1332` → IBAN

**Détecté (2) :**
- `ES91 2100 0418 4502 000` → IBAN
- `5 1332` → CADASTRAL_REF

**Résultat :** 1 corrects, 0 manqués, 1 faux positifs

**Notes :** Format IBAN standard avec espaces

---

#### phone_international [FAIL]

**Difficulté :** medium

**Texte :**
```
Contacto: +34 612 345 678 o 0034612345678.
```

**Attendu (2) :**
- `+34 612 345 678` → PHONE
- `0034612345678` → PHONE

**Détecté (1) :**
- `+34 612 345 678` → PHONE

**Résultat :** 1 corrects, 1 manqués, 0 faux positifs

**Notes :** Formats de téléphone internationaux

---

#### date_roman_numerals [FAIL]

**Difficulté :** hard

**Texte :**
```
Otorgado el día XV de marzo del año MMXXIV.
```

**Attendu (1) :**
- `XV de marzo del año MMXXIV` → DATE

**Détecté (0) :**
- (aucune entité)

**Résultat :** 0 corrects, 1 manqués, 0 faux positifs

**Notes :** Date avec chiffres romains (style notarial)

---

#### date_ordinal [PASS]

**Difficulté :** medium

**Texte :**
```
El primero de enero de dos mil veinticuatro.
```

**Attendu (1) :**
- `primero de enero de dos mil veinticuatro` → DATE

**Détecté (2) :**
- `El` → DATE
- `primero de enero de dos mil veinticuatro` → DATE

**Résultat :** 1 corrects, 0 manqués, 1 faux positifs

**Notes :** Date entièrement écrite en toutes lettres

---

#### address_floor_door [PASS]

**Difficulté :** medium

**Texte :**
```
Domicilio en Calle Mayor 15, 3º B, 28001 Madrid.
```

**Attendu (3) :**
- `Calle Mayor 15, 3º B` → ADDRESS
- `28001` → POSTAL_CODE
- `Madrid` → LOCATION

**Détecté (3) :**
- `Calle Mayor 15, 3º B` → ADDRESS
- `28` → POSTAL_CODE
- `Madrid` → LOCATION

**Résultat :** 3 corrects, 0 manqués, 0 faux positifs

**Notes :** Adresse avec étage et porte

---

### ADVERSARIAL

#### negation_dni [PASS]

**Difficulté :** hard

**Texte :**
```
El interesado manifiesta NO tener DNI ni NIE.
```

**Attendu (0) :**
- (aucune entité)

**Détecté (0) :**
- (aucune entité)

**Résultat :** 0 corrects, 0 manqués, 0 faux positifs

**Notes :** Ne devrait PAS détecter de PII - contexte de négation

---

#### example_dni [FAIL]

**Difficulté :** hard

**Texte :**
```
El formato del DNI es 12345678X (ejemplo ilustrativo).
```

**Attendu (0) :**
- (aucune entité)

**Détecté (1) :**
- `12345678X` → DNI_NIE

**Résultat :** 0 corrects, 0 manqués, 1 faux positifs

**Notes :** Exemple/contexte illustratif devrait être ignoré

---

#### fictional_person [FAIL]

**Difficulté :** hard

**Texte :**
```
Como dijo Don Quijote de la Mancha en su célebre obra.
```

**Attendu (0) :**
- (aucune entité)

**Détecté (1) :**
- `Don Quijote de la Mancha` → PERSON

**Résultat :** 0 corrects, 0 manqués, 1 faux positifs

**Notes :** Personnage fictif/littéraire - pas de PII

---

#### organization_as_person [PASS]

**Difficulté :** medium

**Texte :**
```
García y Asociados, S.L. interpone demanda.
```

**Attendu (1) :**
- `García y Asociados, S.L.` → ORGANIZATION

**Détecté (1) :**
- `García y Asociados, S.L.` → ORGANIZATION

**Résultat :** 1 corrects, 0 manqués, 0 faux positifs

**Notes :** Nom de famille dans le nom de l'entreprise - devrait être ORG et non PERSON

---

#### location_as_person [PASS]

**Difficulté :** hard

**Texte :**
```
El municipio de San Fernando del Valle de Catamarca.
```

**Attendu (1) :**
- `San Fernando del Valle de Catamarca` → LOCATION

**Détecté (1) :**
- `San Fernando del Valle de Catamarca` → LOCATION

**Résultat :** 1 corrects, 0 manqués, 0 faux positifs

**Notes :** Lieu avec préfixe de personne (San)

---

#### date_in_reference [FAIL]

**Difficulté :** hard

**Texte :**
```
Según la Ley 15/2022, de 12 de julio, reguladora...
```

**Attendu (0) :**
- (aucune entité)

**Détecté (5) :**
- `Ley` → ECLI
- `15` → PROFESSIONAL_ID
- `/` → ECLI
- `2022` → PROFESSIONAL_ID
- `,` → ECLI

**Résultat :** 0 corrects, 0 manqués, 5 faux positifs

**Notes :** Date dans une référence légale - pas une PII autonome

---

#### numbers_not_dni [PASS]

**Difficulté :** medium

**Texte :**
```
El expediente 12345678 consta de 9 folios.
```

**Attendu (0) :**
- (aucune entité)

**Détecté (1) :**
- `12345678` → PROFESSIONAL_ID

**Résultat :** 0 corrects, 0 manqués, 1 faux positifs

**Notes :** Numéro à 8 chiffres qui n'est PAS un DNI (dossier)

---

#### mixed_languages [PASS]

**Difficulté :** hard

**Texte :**
```
Mr. John Smith, con pasaporte UK123456789, residente en Madrid.
```

**Attendu (3) :**
- `John Smith` → PERSON
- `UK123456789` → DNI_NIE
- `Madrid` → LOCATION

**Détecté (3) :**
- `Mr. John Smith` → PERSON
- `UK123456789` → DNI_NIE
- `Madrid` → LOCATION

**Résultat :** 3 corrects, 0 manqués, 0 faux positifs

**Notes :** Nom anglais et passeport étranger

---

### CORRUPTION OCR

#### ocr_letter_substitution [PASS]

**Difficulté :** medium

**Texte :**
```
DNl 12345678Z perteneciente a María García.
```

**Attendu (2) :**
- `12345678Z` → DNI_NIE
- `María García` → PERSON

**Détecté (2) :**
- `12345678Z` → DNI_NIE
- `María García` → PERSON

**Résultat :** 2 corrects, 0 manqués, 0 faux positifs

**Notes :** OCR a confondu I avec l

---

#### ocr_zero_o_confusion [FAIL]

**Difficulté :** hard

**Texte :**
```
IBAN ES91 21O0 0418 45O2 OOO5 1332.
```

**Attendu (1) :**
- `ES91 21O0 0418 45O2 OOO5 1332` → IBAN

**Détecté (0) :**
- (aucune entité)

**Résultat :** 0 corrects, 1 manqués, 0 faux positifs

**Notes :** OCR a confondu 0 avec O

---

#### ocr_missing_spaces [FAIL]

**Difficulté :** hard

**Texte :**
```
DonJoséGarcíaLópezconDNI12345678X.
```

**Attendu (2) :**
- `JoséGarcíaLópez` → PERSON
- `12345678X` → DNI_NIE

**Détecté (1) :**
- `DonJoséGarcíaLópezcon` → PERSON

**Résultat :** 1 corrects, 1 manqués, 0 faux positifs

**Notes :** OCR a perdu tous les espaces

---

#### ocr_extra_spaces [FAIL]

**Difficulté :** hard

**Texte :**
```
D N I  1 2 3 4 5 6 7 8 Z  de  M a r í a.
```

**Attendu (2) :**
- `1 2 3 4 5 6 7 8 Z` → DNI_NIE
- `M a r í a` → PERSON

**Détecté (0) :**
- (aucune entité)

**Résultat :** 0 corrects, 2 manqués, 0 faux positifs

**Notes :** OCR a ajouté des espaces supplémentaires

---

#### ocr_accent_loss [PASS]

**Difficulté :** easy

**Texte :**
```
Jose Maria Garcia Lopez, vecino de Malaga.
```

**Attendu (2) :**
- `Jose Maria Garcia Lopez` → PERSON
- `Malaga` → LOCATION

**Détecté (2) :**
- `Jose Maria Garcia Lopez` → PERSON
- `Malaga` → LOCATION

**Résultat :** 2 corrects, 0 manqués, 0 faux positifs

**Notes :** OCR a perdu les accents (fréquent)

---

### ÉVASION UNICODE

#### cyrillic_o [PASS]

**Difficulté :** hard

**Texte :**
```
DNI 12345678Х pertenece a María.
```

**Attendu (2) :**
- `12345678Х` → DNI_NIE
- `María` → PERSON

**Détecté (2) :**
- `12345678` → DNI_NIE
- `María` → PERSON

**Résultat :** 2 corrects, 0 manqués, 0 faux positifs

**Notes :** Х cyrillique (U+0425) au lieu du X latin

---

#### zero_width_space [FAIL]

**Difficulté :** hard

**Texte :**
```
DNI 123​456​78Z de María García.
```

**Attendu (2) :**
- `12345678Z` → DNI_NIE
- `María García` → PERSON

**Détecté (3) :**
- `123​456​78Z` → DNI_NIE
- `de` → PERSON
- `María García` → PERSON

**Résultat :** 2 corrects, 0 manqués, 1 faux positifs

**Notes :** Espaces sans chasse insérés (U+200B)

---

#### fullwidth_numbers [FAIL]

**Difficulté :** hard

**Texte :**
```
DNI １２３４５６７８Z de María.
```

**Attendu (2) :**
- `１２３４５６７８Z` → DNI_NIE
- `María` → PERSON

**Détecté (0) :**
- (aucune entité)

**Résultat :** 0 corrects, 2 manqués, 0 faux positifs

**Notes :** Chiffres pleine chasse (U+FF11-U+FF19)

---

### MONDE RÉEL (REAL WORLD)

#### notarial_header [FAIL]

**Difficulté :** medium

**Texte :**
```
NÚMERO MIL DOSCIENTOS TREINTA Y CUATRO.- En la ciudad de Sevilla, a quince de marzo de dos mil veinticuatro, ante mí, JOSÉ GARCÍA LÓPEZ, Notario del Ilustre Colegio de Sevilla.
```

**Attendu (4) :**
- `Sevilla` → LOCATION
- `quince de marzo de dos mil veinticuatro` → DATE
- `JOSÉ GARCÍA LÓPEZ` → PERSON
- `Sevilla` → LOCATION

**Détecté (3) :**
- `Sevilla` → LOCATION
- `JOSÉ GARCÍA LÓPEZ` → PERSON
- `Sevilla` → LOCATION

**Résultat :** 3 corrects, 1 manqués, 0 faux positifs

**Notes :** En-tête d'acte notarié standard

---

#### testament_comparecencia [PASS]

**Difficulté :** hard

**Texte :**
```
COMPARECE: Doña MARÍA ANTONIA FERNÁNDEZ RUIZ, mayor de edad, viuda, natural de Córdoba, vecina de Madrid, con domicilio en Calle Alcalá número 123, piso 4º, puerta B, y con D.N.I. número 12345678-Z.
```

**Attendu (5) :**
- `MARÍA ANTONIA FERNÁNDEZ RUIZ` → PERSON
- `Córdoba` → LOCATION
- `Madrid` → LOCATION
- `Calle Alcalá número 123, piso 4º, puerta B` → ADDRESS
- `12345678-Z` → DNI_NIE

**Détecté (5) :**
- `Doña MARÍA ANTONIA FERNÁNDEZ RUIZ` → PERSON
- `Córdoba` → LOCATION
- `Madrid` → LOCATION
- `Calle Alcalá número 123, piso 4º, puerta B,` → ADDRESS
- `12345678-Z` → DNI_NIE

**Résultat :** 5 corrects, 0 manqués, 0 faux positifs

**Notes :** Clause de comparution testamentaire

---

#### judicial_sentence_header [FAIL]

**Difficulté :** hard

**Texte :**
```
SENTENCIA Nº 123/2024. En Madrid, a diez de enero de dos mil veinticuatro. Vistos por la Sala Primera del Tribunal Supremo los recursos interpuestos por D. ANTONIO PÉREZ MARTÍNEZ, representado por el Procurador D. CARLOS SÁNCHEZ GÓMEZ.
```

**Attendu (4) :**
- `Madrid` → LOCATION
- `diez de enero de dos mil veinticuatro` → DATE
- `ANTONIO PÉREZ MARTÍNEZ` → PERSON
- `CARLOS SÁNCHEZ GÓMEZ` → PERSON

**Détecté (5) :**
- `Nº 123/2024` → PROFESSIONAL_ID
- `Madrid` → LOCATION
- `Sala Primera del Tribunal Supremo` → ORGANIZATION
- `D. ANTONIO PÉREZ MARTÍNEZ` → PERSON
- `D. CARLOS SÁNCHEZ GÓMEZ` → PERSON

**Résultat :** 3 corrects, 1 manqués, 2 faux positifs

**Notes :** En-tête de jugement de la Cour Suprême

---

#### contract_parties [FAIL]

**Difficulté :** hard

**Texte :**
```
De una parte, INMOBILIARIA GARCÍA, S.L., con CIF B-12345678, domiciliada en Plaza Mayor 1, 28013 Madrid, representada por D. PEDRO GARCÍA LÓPEZ. De otra parte, Dña. ANA MARTÍNEZ RUIZ, con NIF 87654321-X.
```

**Attendu (8) :**
- `INMOBILIARIA GARCÍA, S.L.` → ORGANIZATION
- `B-12345678` → DNI_NIE
- `Plaza Mayor 1` → ADDRESS
- `28013` → POSTAL_CODE
- `Madrid` → LOCATION
- `PEDRO GARCÍA LÓPEZ` → PERSON
- `ANA MARTÍNEZ RUIZ` → PERSON
- `87654321-X` → DNI_NIE

**Détecté (6) :**
- `INMOBILIARIA GARCÍA, S.L.,` → ORGANIZATION
- `B-12345678` → DNI_NIE
- `Plaza Mayor 1, 28013 Madrid` → ADDRESS
- `D. PEDRO GARCÍA LÓPEZ` → PERSON
- `Dña. ANA MARTÍNEZ RUIZ` → PERSON
- `87654321-X` → DNI_NIE

**Résultat :** 6 corrects, 2 manqués, 0 faux positifs

**Notes :** Clause des parties au contrat

---

#### bank_account_clause [FAIL]

**Difficulté :** medium

**Texte :**
```
El pago se efectuará mediante transferencia a la cuenta IBAN ES12 0049 1234 5012 3456 7890 titularidad de CONSTRUCCIONES PÉREZ, S.A., con CIF A-98765432.
```

**Attendu (3) :**
- `ES12 0049 1234 5012 3456 7890` → IBAN
- `CONSTRUCCIONES PÉREZ, S.A.` → ORGANIZATION
- `A-98765432` → DNI_NIE

**Détecté (2) :**
- `IBAN ES12 0049 1234 5012 3456 7890` → IBAN
- `CONSTRUCCIONES PÉREZ, S.A.,` → ORGANIZATION

**Résultat :** 2 corrects, 1 manqués, 0 faux positifs

**Notes :** Clause de virement bancaire

---

#### cadastral_reference [PASS]

**Difficulté :** medium

**Texte :**
```
Finca registral número 12345 del Registro de la Propiedad de Málaga, con referencia catastral 1234567AB1234S0001AB.
```

**Attendu (2) :**
- `Málaga` → LOCATION
- `1234567AB1234S0001AB` → CADASTRAL_REF

**Détecté (2) :**
- `Málaga` → LOCATION
- `1234567AB1234S0001AB` → CADASTRAL_REF

**Résultat :** 2 corrects, 0 manqués, 0 faux positifs

**Notes :** Enregistrement de propriété avec référence cadastrale

---

#### professional_ids [FAIL]

**Difficulté :** hard

**Texte :**
```
Interviene el Abogado D. LUIS SÁNCHEZ, colegiado nº 12345 del ICAM, y el Procurador D. MIGUEL TORRES, colegiado nº 67890 del Colegio de Procuradores de Madrid.
```

**Attendu (4) :**
- `LUIS SÁNCHEZ` → PERSON
- `12345` → PROFESSIONAL_ID
- `MIGUEL TORRES` → PERSON
- `67890` → PROFESSIONAL_ID

**Détecté (2) :**
- `Abogado D. LUIS SÁNCHEZ` → PERSON
- `Colegio de Procuradores de Madrid` → ORGANIZATION

**Résultat :** 1 corrects, 3 manqués, 1 faux positifs

**Notes :** Numéros de barreau professionnel

---

#### ecli_citation [PASS]

**Difficulté :** easy

**Texte :**
```
Según doctrina del Tribunal Supremo (ECLI:ES:TS:2023:1234), confirmada en ECLI:ES:AN:2024:567.
```

**Attendu (2) :**
- `ECLI:ES:TS:2023:1234` → ECLI
- `ECLI:ES:AN:2024:567` → ECLI

**Détecté (3) :**
- `Tribunal Supremo` → ORGANIZATION
- `(ECLI:ES:TS:2023:1234),` → ECLI
- `ECLI:ES:AN:2024:567` → ECLI

**Résultat :** 2 corrects, 0 manqués, 1 faux positifs

**Notes :** Citations d'arrêts ECLI

---

#### vehicle_clause [PASS]

**Difficulté :** medium

**Texte :**
```
El vehículo marca SEAT, modelo Ibiza, matrícula 1234 ABC, propiedad de D. FRANCISCO LÓPEZ.
```

**Attendu (2) :**
- `1234 ABC` → LICENSE_PLATE
- `FRANCISCO LÓPEZ` → PERSON

**Détecté (3) :**
- `SEAT` → LICENSE_PLATE
- `matrícula 1234 ABC` → LICENSE_PLATE
- `D. FRANCISCO LÓPEZ` → PERSON

**Résultat :** 2 corrects, 0 manqués, 1 faux positifs

**Notes :** Clause de description de véhicule

---

#### social_security [PASS]

**Difficulté :** easy

**Texte :**
```
Trabajador afiliado a la Seguridad Social con número 281234567890, adscrito al Régimen General.
```

**Attendu (1) :**
- `281234567890` → NSS

**Détecté (2) :**
- `28` → DNI_NIE
- `1234567890` → NSS

**Résultat :** 1 corrects, 0 manqués, 1 faux positifs

**Notes :** Numéro de sécurité sociale dans le contexte de l'emploi

---


## Conclusions

### Points Forts du Modèle

(Analyser les tests réussis et les modèles)

### Faiblesses Identifiées

(Analyser les tests échoués et les modèles)

### Recommandations

1. (Basées sur les résultats)

---

**Généré automatiquement par :** `scripts/adversarial/evaluate_adversarial.py`
