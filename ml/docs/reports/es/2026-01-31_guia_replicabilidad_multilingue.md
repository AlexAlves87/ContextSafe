# Guía de Replicabilidad: Pipeline NER-PII Multilingüe

**Fecha:** 2026-01-31
**Autor:** AlexAlves87
**Proyecto:** ContextSafe ML - Expansión Multilingüe
**Versión:** 1.0.0

---

## 1. Resumen Ejecutivo

Este documento describe cómo replicar el pipeline híbrido NER-PII de ContextSafe (español legal, F1 0.788) para otros idiomas europeos. El enfoque es **modular**: cada componente se adapta al idioma objetivo manteniendo la arquitectura probada.

### Lección Aprendida (LoRA experiment)

| Enfoque | F1 Adversarial | Veredicto |
|---------|----------------|-----------|
| LoRA fine-tuning puro | 0.016 | ❌ Overfitting severo |
| Pipeline híbrido (5 elementos) | **0.788** | ✅ Generaliza bien |

> **Conclusión:** El fine-tuning de transformers sin el pipeline híbrido no generaliza a casos adversariales. Los 5 elementos de post-procesamiento son **esenciales**.

---

## 2. Arquitectura del Pipeline (Idioma-Agnóstica)

```
┌─────────────────────────────────────────────────────────────────┐
│                     PIPELINE HÍBRIDO NER-PII                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Texto entrada                                                   │
│       ↓                                                          │
│  ┌────────────────────────────────────────┐                      │
│  │ [1] TextNormalizer                     │ ← Idioma-agnóstico   │
│  │     - Unicode NFKC                     │                      │
│  │     - Homoglyphs (Cyrillic→Latin)      │                      │
│  │     - Zero-width removal               │                      │
│  └────────────────────────────────────────┘                      │
│       ↓                                                          │
│  ┌────────────────────────────────────────┐                      │
│  │ [NER] Transformer LegalBERT            │ ← ADAPTAR POR IDIOMA │
│  │     - ES: RoBERTa-BNE CAPITEL NER      │                      │
│  │     - EN: Legal-BERT                   │                      │
│  │     - FR: JuriBERT                     │                      │
│  │     - IT: Italian-Legal-BERT           │                      │
│  │     - PT: Legal-BERTimbau              │                      │
│  │     - DE: German-Legal-BERT            │                      │
│  └────────────────────────────────────────┘                      │
│       ↓                                                          │
│  ┌────────────────────────────────────────┐                      │
│  │ [2] Checksum Validators                │ ← ADAPTAR POR PAÍS   │
│  │     - Algoritmos de verificación       │                      │
│  │     - Ajuste de confianza              │                      │
│  └────────────────────────────────────────┘                      │
│       ↓                                                          │
│  ┌────────────────────────────────────────┐                      │
│  │ [3] Regex Patterns                     │ ← ADAPTAR POR PAÍS   │
│  │     - IDs nacionales                   │                      │
│  │     - Formatos con espacios/guiones    │                      │
│  └────────────────────────────────────────┘                      │
│       ↓                                                          │
│  ┌────────────────────────────────────────┐                      │
│  │ [4] Date Patterns                      │ ← ADAPTAR POR IDIOMA │
│  │     - Meses en idioma local            │                      │
│  │     - Formatos legales/notariales      │                      │
│  └────────────────────────────────────────┘                      │
│       ↓                                                          │
│  ┌────────────────────────────────────────┐                      │
│  │ [5] Boundary Refinement                │ ← ADAPTAR POR IDIOMA │
│  │     - Prefijos honoríficos             │                      │
│  │     - Sufijos de organización          │                      │
│  └────────────────────────────────────────┘                      │
│       ↓                                                          │
│  Entidades finales                                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Componentes por Tipo de Adaptación

| Componente | Adaptación | Esfuerzo |
|------------|------------|----------|
| TextNormalizer | Ninguna (universal) | 0 |
| Transformer NER | Cambiar modelo base | Bajo |
| Checksum Validators | Algoritmos por país | Medio |
| Regex Patterns | Patrones por país | Alto |
| Date Patterns | Meses/formatos por idioma | Medio |
| Boundary Refinement | Prefijos/sufijos por idioma | Medio |

---

## 3. Modelos Base Recomendados por Idioma

### 3.1 Modelos Monolingües (Máximo Rendimiento)

| Idioma | Modelo | HuggingFace | Params | Corpus |
|--------|--------|-------------|--------|--------|
| 🇪🇸 Español | RoBERTa-BNE CAPITEL NER | `PlanTL-GOB-ES/roberta-base-bne-capitel-ner` | 125M | BNE + CAPITEL NER |
| 🇬🇧 Inglés | Legal-BERT | `nlpaueb/legal-bert-base-uncased` | 110M | 12GB legal |
| 🇫🇷 Francés | JuriBERT | `dascim/juribert-base` | 110M | Légifrance |
| 🇮🇹 Italiano | Italian-Legal-BERT | `dlicari/Italian-Legal-BERT` | 110M | Giurisprudenza |
| 🇵🇹 Portugués | Legal-BERTimbau | `rufimelo/Legal-BERTimbau-base` | 110M | 30K docs |
| 🇩🇪 Alemán | German-Legal-BERT | `elenanereiss/bert-german-legal` | 110M | Bundesrecht |

### 3.2 Modelo Multilingüe (Rápido Despliegue)

| Modelo | HuggingFace | Params | Idiomas |
|--------|-------------|--------|---------|
| Legal-XLM-RoBERTa | `joelniklaus/legal-xlm-roberta-large` | 355M | 24 idiomas |

**Trade-off:**
- Monolingüe: +2-5% F1, requiere modelo por idioma
- Multilingüe: Un solo modelo, ligeramente menor rendimiento

---

## 4. Adaptaciones por País

### 4.1 España (Implementado ✅)

#### Identificadores Nacionales

| Tipo | Formato | Checksum | Regex |
|------|---------|----------|-------|
| DNI | 8 dígitos + letra | mod 23 | `\d{8}[A-Z]` |
| NIE | X/Y/Z + 7 dígitos + letra | mod 23 | `[XYZ]\d{7}[A-Z]` |
| CIF | Letra + 7 dígitos + control | suma pares/impares | `[A-W]\d{7}[0-9A-J]` |
| IBAN | ES + 22 caracteres | ISO 13616 mod 97 | `ES\d{2}[\d\s]{20}` |
| NSS | 12 dígitos | mod 97 | `\d{12}` |
| Matrícula | 4 dígitos + 3 letras | ninguno | `\d{4}[BCDFGHJKLMNPRSTVWXYZ]{3}` |

#### Prefijos Honoríficos

```python
PREFIXES_ES = [
    "Don", "Doña", "D.", "Dña.", "D.ª",
    "Sr.", "Sra.", "Srta.",
    "Ilmo.", "Ilma.", "Excmo.", "Excma.",
]
```

#### Meses

```python
MONTHS_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
]
```

---

### 4.2 Francia 🇫🇷

#### Identificadores Nacionales

| Tipo | Formato | Checksum | Regex |
|------|---------|----------|-------|
| NIR (Sécu) | 15 dígitos | mod 97 | `[12]\d{2}(0[1-9]|1[0-2])\d{2}\d{3}\d{3}\d{2}` |
| SIRET | 14 dígitos | Luhn | `\d{14}` |
| SIREN | 9 dígitos | Luhn | `\d{9}` |
| IBAN | FR + 25 caracteres | ISO 13616 | `FR\d{2}[\d\s]{23}` |
| Carte ID | 12 caracteres | ninguno | `[A-Z0-9]{12}` |

#### Prefijos Honoríficos

```python
PREFIXES_FR = [
    "Monsieur", "Madame", "Mademoiselle",
    "M.", "Mme", "Mlle",
    "Maître", "Me", "Me.",
    "Docteur", "Dr", "Dr.",
]
```

#### Meses

```python
MONTHS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre"
]
```

#### Sufijos Organización

```python
ORG_SUFFIXES_FR = [
    "S.A.", "SA", "S.A.S.", "SAS", "S.A.R.L.", "SARL",
    "S.C.I.", "SCI", "E.U.R.L.", "EURL", "S.N.C.", "SNC",
]
```

---

### 4.3 Italia 🇮🇹

#### Identificadores Nacionales

| Tipo | Formato | Checksum | Regex |
|------|---------|----------|-------|
| Codice Fiscale | 16 caracteres | mod 26 especial | `[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]` |
| Partita IVA | 11 dígitos | Luhn variante | `\d{11}` |
| IBAN | IT + 25 caracteres | ISO 13616 | `IT\d{2}[A-Z][\d\s]{22}` |
| Carta Identità | 2 letras + 7 dígitos | ninguno | `[A-Z]{2}\d{7}` |

#### Checksum Codice Fiscale

```python
def validate_codice_fiscale(cf: str) -> bool:
    """Algoritmo mod 26 con valores especiales para posiciones pares/impares."""
    ODD_VALUES = {'0': 1, '1': 0, '2': 5, ...}  # Tabla completa
    EVEN_VALUES = {'0': 0, '1': 1, '2': 2, ...}
    # Sum odd positions with ODD_VALUES, even with EVEN_VALUES
    # Control letter = chr(ord('A') + total % 26)
```

#### Prefijos Honoríficos

```python
PREFIXES_IT = [
    "Signor", "Signora", "Signorina",
    "Sig.", "Sig.ra", "Sig.na",
    "Dott.", "Dott.ssa", "Avv.", "Ing.",
    "On.", "Sen.", "Onorevole",
]
```

#### Meses

```python
MONTHS_IT = [
    "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
    "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"
]
```

---

### 4.4 Portugal 🇵🇹

#### Identificadores Nacionales

| Tipo | Formato | Checksum | Regex |
|------|---------|----------|-------|
| NIF | 9 dígitos | mod 11 | `[123568]\d{8}` |
| CC (Cartão Cidadão) | 8 dígitos + 1 letra + 2 dígitos | mod 11 + letra | `\d{8}[A-Z]\d{2}` |
| NISS | 11 dígitos | mod 10 | `\d{11}` |
| IBAN | PT + 23 caracteres | ISO 13616 | `PT\d{2}[\d\s]{21}` |

#### Checksum NIF Portugal

```python
def validate_nif_pt(nif: str) -> bool:
    """Algoritmo mod 11 con pesos decrecientes."""
    weights = [9, 8, 7, 6, 5, 4, 3, 2]
    total = sum(int(d) * w for d, w in zip(nif[:8], weights))
    control = 11 - (total % 11)
    if control >= 10:
        control = 0
    return int(nif[8]) == control
```

#### Prefijos Honoríficos

```python
PREFIXES_PT = [
    "Senhor", "Senhora", "Sr.", "Sra.", "Srª",
    "Dom", "Dona", "D.",
    "Doutor", "Doutora", "Dr.", "Dra.",
    "Exmo.", "Exma.",
]
```

---

### 4.5 Alemania 🇩🇪

#### Identificadores Nacionales

| Tipo | Formato | Checksum | Regex |
|------|---------|----------|-------|
| Steuer-ID | 11 dígitos | ISO 7064 mod 11-10 | `\d{11}` |
| Personalausweis | 10 caracteres | mod 10 especial | `[A-Z0-9]{10}` |
| IBAN | DE + 20 caracteres | ISO 13616 | `DE\d{2}[\d\s]{18}` |
| Handelsregister | HRA/HRB + número | ninguno | `HR[AB]\s?\d+` |

#### Prefijos Honoríficos

```python
PREFIXES_DE = [
    "Herr", "Frau",
    "Dr.", "Prof.", "Prof. Dr.",
    "Rechtsanwalt", "RA", "Notar",
]
```

#### Meses

```python
MONTHS_DE = [
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember"
]
```

---

### 4.6 Reino Unido 🇬🇧

#### Identificadores Nacionales

| Tipo | Formato | Checksum | Regex |
|------|---------|----------|-------|
| NI Number | 2 letras + 6 dígitos + letra | ninguno validable | `[A-Z]{2}\d{6}[A-D]` |
| Company Number | 8 caracteres | ninguno | `[A-Z]{2}\d{6}|[\d]{8}` |
| IBAN | GB + 22 caracteres | ISO 13616 | `GB\d{2}[A-Z]{4}[\d\s]{14}` |
| Passport | 9 dígitos | ninguno | `\d{9}` |

#### Prefijos Honoríficos

```python
PREFIXES_EN = [
    "Mr", "Mr.", "Mrs", "Mrs.", "Ms", "Ms.", "Miss",
    "Dr", "Dr.", "Prof", "Prof.",
    "Sir", "Dame", "Lord", "Lady",
    "The Honourable", "Hon.",
]
```

---

## 5. Checklist de Implementación por Idioma

### Fase 1: Preparación (1-2 días)

- [ ] **Seleccionar modelo base** de la tabla 3.1
- [ ] **Descargar modelo** a `models/pretrained/{modelo}/`
- [ ] **Verificar carga** con script de prueba
- [ ] **Definir categorías PII** relevantes para el país

### Fase 2: Checksum Validators (2-3 días)

- [ ] **Investigar algoritmos** de validación del país
- [ ] **Implementar validators** en `scripts/preprocess/{country}_validators.py`
- [ ] **Crear tests unitarios** (mínimo 20 casos por tipo)
- [ ] **Documentar algoritmos** con referencias oficiales

### Fase 3: Regex Patterns (3-5 días)

- [ ] **Recopilar formatos oficiales** de IDs del país
- [ ] **Implementar patrones** en `scripts/preprocess/{country}_id_patterns.py`
- [ ] **Incluir variantes** con espacios, guiones, puntos
- [ ] **Tests con ejemplos reales** (anonimizados)

### Fase 4: Date Patterns (1-2 días)

- [ ] **Traducir meses** al idioma objetivo
- [ ] **Adaptar formatos** legales/notariales locales
- [ ] **Implementar** en `scripts/preprocess/{country}_date_patterns.py`
- [ ] **Tests con fechas reales** de documentos legales

### Fase 5: Boundary Refinement (1-2 días)

- [ ] **Compilar lista** de prefijos honoríficos
- [ ] **Compilar lista** de sufijos de organización
- [ ] **Implementar** en `scripts/preprocess/{country}_boundary_refinement.py`
- [ ] **Tests con nombres/orgs** reales

### Fase 6: Gazetteers (2-4 días)

- [ ] **Nombres propios** frecuentes (INE equivalente)
- [ ] **Apellidos** frecuentes
- [ ] **Municipios/ciudades**
- [ ] **Organizaciones** conocidas (empresas, instituciones)

### Fase 7: Test Set Adversarial (2-3 días)

- [ ] **Crear 30-40 casos** específicos del idioma:
  - Edge cases (formatos inusuales)
  - Adversarial (negaciones, ejemplos, ficción)
  - OCR corruption
  - Unicode evasion (ya cubierto)
  - Real world (documentos legales típicos)
- [ ] **Definir expected entities** para cada caso
- [ ] **Ejecutar evaluación SemEval**

### Fase 8: Integración (1-2 días)

- [ ] **Integrar componentes** en `ner_predictor_{lang}.py`
- [ ] **Ejecutar test set adversarial**
- [ ] **Ajustar** hasta F1 ≥ 0.70
- [ ] **Documentar resultados**

---

## 6. Estimación de Esfuerzo Total

| Idioma | Modelo | Complejidad IDs | Esfuerzo Est. |
|--------|--------|-----------------|---------------|
| 🇫🇷 Francés | JuriBERT | Media (NIR, SIRET) | 2-3 semanas |
| 🇮🇹 Italiano | Italian-Legal-BERT | Alta (Codice Fiscale) | 3-4 semanas |
| 🇵🇹 Portugués | Legal-BERTimbau | Media (NIF, CC) | 2-3 semanas |
| 🇩🇪 Alemán | German-Legal-BERT | Media (Steuer-ID) | 2-3 semanas |
| 🇬🇧 Inglés | Legal-BERT | Baja (NI Number) | 1-2 semanas |

**Total para 5 idiomas:** 10-15 semanas (1 desarrollador)
**Con paralelización (2-3 devs):** 4-6 semanas

---

## 7. Estructura de Archivos por Idioma

```
ml/
├── scripts/
│   ├── preprocess/
│   │   ├── spanish_id_patterns.py      # ✅ Implementado
│   │   ├── spanish_date_patterns.py    # ✅ Implementado
│   │   ├── boundary_refinement.py      # ✅ Implementado (adaptar)
│   │   │
│   │   ├── french_id_patterns.py       # Por implementar
│   │   ├── french_date_patterns.py
│   │   ├── french_validators.py
│   │   │
│   │   ├── italian_id_patterns.py      # Por implementar
│   │   ├── italian_date_patterns.py
│   │   ├── italian_validators.py
│   │   │
│   │   └── ... (por idioma)
│   │
│   ├── inference/
│   │   ├── ner_predictor.py            # ✅ Español
│   │   ├── ner_predictor_fr.py         # Por implementar
│   │   ├── ner_predictor_it.py
│   │   └── ...
│   │
│   └── evaluate/
│       ├── test_ner_predictor_adversarial_v2.py  # ✅ Español
│       ├── adversarial_tests_fr.py               # Por implementar
│       └── ...
│
├── gazetteers/
│   ├── es/                             # ✅ Implementado
│   │   ├── nombres.json
│   │   ├── apellidos.json
│   │   └── municipios.json
│   │
│   ├── fr/                             # Por implementar
│   ├── it/
│   ├── pt/
│   ├── de/
│   └── en/
│
└── models/
    └── pretrained/
        ├── legal-xlm-roberta-base/     # ✅ Descargado
        ├── juribert-base/              # Por descargar
        ├── italian-legal-bert/
        └── ...
```

---

## 8. Referencias

### 8.1 Papers y Documentación

| Recurso | URL | Uso |
|---------|-----|-----|
| Legal-BERT Paper | aclanthology.org/2020.findings-emnlp.261 | Arquitectura |
| JuriBERT Paper | aclanthology.org/2021.nllp-1.9 | Francés legal |
| SemEval 2013 Task 9 | aclweb.org/anthology/S13-2013 | Métricas evaluación |
| ISO 13616 (IBAN) | iso.org/standard/81090.html | Checksum IBAN |

### 8.2 Fuentes de Gazetteers por País

| País | Nombres | Municipios | IDs |
|------|---------|------------|-----|
| 🇪🇸 España | INE | INE | BOE |
| 🇫🇷 Francia | INSEE | INSEE | Légifrance |
| 🇮🇹 Italia | ISTAT | ISTAT | Normattiva |
| 🇵🇹 Portugal | INE-PT | INE-PT | DRE |
| 🇩🇪 Alemania | Statistisches Bundesamt | - | Bundesrecht |
| 🇬🇧 Reino Unido | ONS | ONS | legislation.gov.uk |

---

## 9. Lecciones Aprendidas (ContextSafe ES)

### 9.1 Lo que funcionó

1. **Pipeline híbrido > ML puro**: Transformers solos no generalizan a casos adversariales
2. **Regex para formatos variables**: DNI con espacios, IBAN con grupos
3. **Checksum validation**: Reduce falsos positivos significativamente
4. **Boundary refinement**: Convierte PAR→COR (16 casos corregidos)
5. **Test set adversarial**: Detecta problemas antes de producción

### 9.2 Lo que NO funcionó

1. **LoRA fine-tuning sin pipeline**: F1 0.016 en adversarial (overfitting)
2. **GLiNER zero-shot**: F1 0.325 (no conoce formatos españoles)
3. **Confiar solo en métricas de dev set**: 0.989 dev vs 0.016 adversarial

### 9.3 Recomendaciones

1. **Siempre crear test set adversarial** antes de declarar "listo"
2. **Implementar checksum validators** para todos los IDs con verificación matemática
3. **Invertir en gazetteers de calidad** (nombres, municipios)
4. **Documentar cada elemento** con tests standalone

---

## 10. Próximos Pasos

1. **Priorizar idioma** según demanda de mercado
2. **Descargar modelo base** del idioma seleccionado
3. **Adaptar componentes** siguiendo este checklist
4. **Crear test set adversarial** específico
5. **Iterar hasta F1 ≥ 0.70** en adversarial

---

**Generado por:** AlexAlves87
**Fecha:** 2026-01-31
**Versión:** 1.0.0
