# Informe de Estado: Sistema NER-PII para Documentos Legales Españoles

**Fecha:** 2026-01-15
**Versión:** 1.0
**Autor:** AlexAlves87
**Proyecto:** ContextSafe ML - Fine-tuning NER

---

## Resumen Ejecutivo

Este informe documenta el desarrollo del sistema de detección de PII (Personally Identifiable Information) para documentos legales españoles. El sistema debe detectar 13 categorías de entidades con F1 ≥ 0.85.

### Estado Actual

| Fase | Estado | Progreso |
|------|--------|----------|
| Descarga de datos base | Completado | 100% |
| Generación de gazetteers | Completado | 100% |
| Dataset sintético v1 | Descartado | Error crítico |
| Dataset sintético v2 | Completado | 100% |
| Script de entrenamiento | Completado | 100% |
| Entrenamiento del modelo | Pendiente | 0% |

---

## 1. Objetivo del Proyecto

Desarrollar un modelo NER especializado en documentos legales españoles (testamentos, sentencias, escrituras, contratos) capaz de detectar:

| Categoría | Ejemplos | Prioridad |
|-----------|----------|-----------|
| PERSON | Hermógenes Pérez García | Alta |
| DATE | 15 de marzo de 2024 | Alta |
| DNI_NIE | 12345678Z, X1234567A | Alta |
| IBAN | ES9121000418450200051332 | Alta |
| NSS | 281234567890 | Media |
| PHONE | 612 345 678 | Media |
| ADDRESS | Calle Mayor 15, 3º B | Alta |
| POSTAL_CODE | 28001 | Media |
| ORGANIZATION | Banco Santander, S.A. | Alta |
| LOCATION | Madrid, Comunidad de Madrid | Media |
| ECLI | ECLI:ES:TS:2024:1234 | Baja |
| LICENSE_PLATE | 1234 ABC | Baja |
| CADASTRAL_REF | 1234567AB1234S0001AB | Baja |
| PROFESSIONAL_ID | Colegiado nº 12345 | Baja |

---

## 2. Datos Descargados

### 2.1 Fuentes Oficiales

| Recurso | Ubicación | Tamaño | Descripción |
|---------|-----------|--------|-------------|
| CoNLL-2002 Spanish | `data/raw/conll2002/` | 4.0 MB | Corpus NER estándar |
| INE Nombres por década | `data/raw/gazetteers_ine/nombres_por_fecha.xls` | 1.1 MB | Frecuencia temporal |
| INE Nombres frecuentes | `data/raw/gazetteers_ine/nombres_mas_frecuentes.xls` | 278 KB | Top nombres |
| INE Apellidos | `data/raw/gazetteers_ine/apellidos_frecuencia.xls` | 12 MB | 27,251 apellidos |
| INE Municipios 2024 | `data/raw/municipios/municipios_2024.xlsx` | 300 KB | 8,115 municipios |
| Códigos postales | `data/raw/codigos_postales/codigos_postales.csv` | 359 KB | 11,051 CPs |
| ai4privacy/pii-masking-300k | `data/raw/ai4privacy/` | ~100 MB | Transfer learning |

### 2.2 Modelo Base

| Modelo | Ubicación | Tamaño | F1 Base |
|--------|-----------|--------|---------|
| roberta-base-bne-capitel-ner | `models/checkpoints/` | ~500 MB | 88.5% (CAPITEL) |

**Decisión de modelo:** Se evaluó MEL (Modelo Español Legal) pero carece de fine-tuning NER. Se seleccionó RoBERTa-BNE-capitel-ner por su especialización en NER español.

---

## 3. Gazetteers Generados

### 3.1 Scripts de Generación

| Script | Función | Output |
|--------|---------|--------|
| `parse_ine_gazetteers.py` | Parsea Excel INE → JSON | apellidos.json, nombres_*.json |
| `generate_archaic_names.py` | Genera nombres arcaicos legales | nombres_arcaicos.json |
| `generate_textual_dates.py` | Fechas en formato legal | fechas_textuales.json |
| `generate_administrative_ids.py` | DNI, NIE, IBAN, NSS con checksums inválidos | identificadores_administrativos.json |
| `generate_addresses.py` | Direcciones completas españolas | direcciones.json |
| `generate_organizations.py` | Empresas, juzgados, bancos | organizaciones.json |

### 3.2 Archivos Generados

| Archivo | Tamaño | Contenido |
|---------|--------|-----------|
| `apellidos.json` | 1.8 MB | 27,251 apellidos con frecuencias INE |
| `codigos_postales.json` | 1.2 MB | 11,051 códigos postales |
| `municipios.json` | 164 KB | 8,115 municipios españoles |
| `nombres_hombres.json` | 40 KB | 550 nombres masculinos por década |
| `nombres_mujeres.json` | 41 KB | 550 nombres femeninos por década |
| `nombres_todos.json` | 3.9 KB | 260 nombres únicos (INE) |
| `nombres_arcaicos.json` | 138 KB | 940 nombres arcaicos + 5,070 combinaciones |
| `nombres_arcaicos_flat.json` | 267 KB | Lista plana para NER |
| `fechas_textuales.json` | 159 KB | 645 fechas con 41 patrones legales |
| `fechas_textuales_flat.json` | 86 KB | Lista plana |
| `identificadores_administrativos.json` | 482 KB | 2,550 IDs sintéticos |
| `identificadores_administrativos_flat.json` | 134 KB | Lista plana |
| `direcciones.json` | 159 KB | 600 direcciones + 416 con contexto legal |
| `direcciones_flat.json` | 59 KB | Lista plana |
| `organizaciones.json` | 185 KB | 1,000 organizaciones |
| `organizaciones_flat.json` | 75 KB | Lista plana |

**Total gazetteers:** ~4.9 MB

### 3.3 Características Especiales

**Nombres Arcaicos:** Incluye nombres frecuentes en documentos legales históricos:
- Hermógenes, Segismundo, Práxedes, Gertrudis, Baldomero, Saturnino, Patrocinio...
- Combinaciones compuestas: María del Carmen, José Antonio, Juan de Dios...

**Identificadores Administrativos:** Generados con checksums MATEMÁTICAMENTE INVÁLIDOS:
- DNI: Letra de control incorrecta (mod-23 incorrecto)
- NIE: Prefijo X/Y/Z con letra incorrecta
- IBAN: Dígitos de control "00" (siempre inválido)
- NSS: Control digits incorrectos (mod-97)

Esto garantiza que ningún identificador sintético corresponda a datos reales.

---

## 4. Dataset Sintético

### 4.1 Dataset v1 - ERROR CRÍTICO (DESCARTADO)

**Fecha:** 2026-01-15

El primer dataset generado contenía errores críticos que habrían degradado significativamente el modelo.

#### Error 1: Puntuación Adherida a Tokens

**Problema:** La tokenización simple por espacios en blanco causaba que la puntuación quedara adherida a las entidades.

**Ejemplo del error:**
```
Texto: "Don Hermógenes Freijanes, con DNI 73364386X."
Tokens: ["Don", "Hermógenes", "Freijanes,", "con", "DNI", "73364386X."]
Labels: ["O",   "B-PERSON",   "I-PERSON",   "O",   "O",   "B-DNI_NIE"]
```

**Impacto:** El modelo aprendería que "Freijanes," (con coma) es una persona, pero durante inferencia no reconocería "Freijanes" sin coma.

**Estadísticas del error:**
- 6,806 tokens con puntuación adherida
- Afectaba principalmente a: PERSON, DNI_NIE, IBAN, PHONE
- ~30% de las entidades comprometidas

#### Error 2: Sin Alineación de Subwords

**Problema:** Las etiquetas BIO estaban a nivel de palabra, pero BERT usa tokenización de subwords.

**Ejemplo del error:**
```
Palabra: "Hermógenes"
Subwords: ["Her", "##mó", "##genes"]
Label v1: Solo una etiqueta para toda la palabra → ¿cuál subword la recibe?
```

**Impacto:** Sin alineación explícita, el modelo no podría aprender correctamente la relación entre subwords y etiquetas.

#### Error 3: Desequilibrio de Entidades

| Entidad | Porcentaje v1 | Problema |
|---------|---------------|----------|
| PERSON | 30.3% | Sobrerrepresentado |
| ADDRESS | 12.6% | OK |
| DNI_NIE | 10.1% | OK |
| NSS | 1.7% | Subrepresentado |
| ECLI | 1.7% | Subrepresentado |
| LICENSE_PLATE | 1.7% | Subrepresentado |

### 4.2 Dataset v2 - CORREGIDO

**Fecha:** 2026-01-15

**Script:** `scripts/preprocess/generate_ner_dataset_v2.py`

#### Correcciones Implementadas

**1. Tokenización con HuggingFace:**
```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("PlanTL-GOB-ES/roberta-base-bne")

# La tokenización separa automáticamente la puntuación
# "Freijanes," → ["Fre", "##ij", "##anes", ","]
```

**2. Alineación con word_ids():**
```python
def align(self, sentence, max_length=128):
    encoding = self.tokenizer(
        text,
        max_length=max_length,
        return_offsets_mapping=True,
    )

    word_ids = encoding.word_ids()

    labels = []
    for i, word_id in enumerate(word_ids):
        if word_id is None:
            labels.append(-100)  # Token especial
        elif word_id != previous_word_id:
            labels.append(entity_label)  # Primer subword
        else:
            labels.append(-100)  # Continuación
```

**3. Templates Balanceados:**
- Añadidos 50+ templates específicos para entidades minoritarias
- Aumentada frecuencia de NSS, ECLI, LICENSE_PLATE, CADASTRAL_REF

#### Estadísticas v2

| Split | Muestras | Tokens Totales |
|-------|----------|----------------|
| Train | 4,925 | ~630,000 |
| Validation | 818 | ~105,000 |
| Test | 818 | ~105,000 |
| **Total** | **6,561** | **~840,000** |

**Distribución de entidades v2:**

| Entidad | Count | % |
|---------|-------|---|
| PERSON | 1,800 | 24.4% |
| ADDRESS | 750 | 10.2% |
| LOCATION | 700 | 9.5% |
| DNI_NIE | 600 | 8.1% |
| DATE | 450 | 6.1% |
| ORGANIZATION | 450 | 6.1% |
| POSTAL_CODE | 200 | 2.7% |
| IBAN | 200 | 2.7% |
| CADASTRAL_REF | 150 | 2.0% |
| PHONE | 150 | 2.0% |
| PROFESSIONAL_ID | 150 | 2.0% |
| ECLI | 100 | 1.4% |
| LICENSE_PLATE | 100 | 1.4% |
| NSS | 100 | 1.4% |

#### Formato de Salida

```
data/processed/ner_dataset_v2/
├── train/
│   ├── data-00000-of-00001.arrow
│   └── dataset_info.json
├── validation/
│   ├── data-00000-of-00001.arrow
│   └── dataset_info.json
├── test/
│   ├── data-00000-of-00001.arrow
│   └── dataset_info.json
├── label_mappings.json
└── dataset_dict.json
```

**Esquema de datos:**
```python
{
    "input_ids": [0, 1234, 5678, ...],      # Token IDs
    "attention_mask": [1, 1, 1, ...],        # Máscara de atención
    "labels": [-100, 1, 2, -100, ...],       # Etiquetas alineadas
}
```

**Etiquetas (29 clases):**
```json
{
    "O": 0,
    "B-PERSON": 1, "I-PERSON": 2,
    "B-LOCATION": 3, "I-LOCATION": 4,
    "B-ORGANIZATION": 5, "I-ORGANIZATION": 6,
    "B-DATE": 7, "I-DATE": 8,
    "B-DNI_NIE": 9, "I-DNI_NIE": 10,
    "B-IBAN": 11, "I-IBAN": 12,
    "B-NSS": 13, "I-NSS": 14,
    "B-PHONE": 15, "I-PHONE": 16,
    "B-ADDRESS": 17, "I-ADDRESS": 18,
    "B-POSTAL_CODE": 19, "I-POSTAL_CODE": 20,
    "B-LICENSE_PLATE": 21, "I-LICENSE_PLATE": 22,
    "B-CADASTRAL_REF": 23, "I-CADASTRAL_REF": 24,
    "B-ECLI": 25, "I-ECLI": 26,
    "B-PROFESSIONAL_ID": 27, "I-PROFESSIONAL_ID": 28
}
```

---

## 5. Configuración de Entrenamiento

### 5.1 Investigación de Mejores Prácticas

Se investigaron las mejores prácticas para fine-tuning de NER basándose en:
- Documentación de HuggingFace
- Papers académicos (RoBERTa, BERT for NER)
- Benchmarks de modelos españoles (CAPITEL, AnCora)

### 5.2 Hyperparámetros Seleccionados

**Archivo:** `scripts/train/train_ner.py`

```python
CONFIG = {
    # Optimización (MÁS IMPORTANTE)
    "learning_rate": 2e-5,          # Grid: {1e-5, 2e-5, 3e-5, 5e-5}
    "weight_decay": 0.01,           # Regularización L2
    "adam_epsilon": 1e-8,           # Estabilidad numérica

    # Batching
    "per_device_train_batch_size": 16,
    "per_device_eval_batch_size": 32,
    "gradient_accumulation_steps": 2,  # Batch efectivo = 32

    # Epochs
    "num_train_epochs": 4,          # Conservador para legal

    # Learning Rate Scheduling
    "warmup_ratio": 0.06,           # 6% warmup (paper RoBERTa)
    "lr_scheduler_type": "linear",  # Decay lineal

    # Early Stopping
    "early_stopping_patience": 2,   # Parar si no mejora 2 evals
    "metric_for_best_model": "f1",

    # Longitud de Secuencia
    "max_length": 384,              # Documentos legales largos

    # Hardware
    "fp16": True,                   # Precisión mixta si GPU
    "dataloader_num_workers": 4,

    # Reproducibilidad
    "seed": 42,
}
```

### 5.3 Justificación de Decisiones

| Parámetro | Valor | Justificación |
|-----------|-------|---------------|
| learning_rate | 2e-5 | Valor estándar para fine-tuning BERT/RoBERTa |
| batch_size | 32 (efectivo) | Balance entre estabilidad y memoria |
| epochs | 4 | Evitar overfitting en datos sintéticos |
| warmup | 6% | Recomendación paper RoBERTa |
| max_length | 384 | Documentos legales pueden ser extensos |
| early_stopping | 2 | Detección temprana de overfitting |

### 5.4 Dependencias

**Archivo:** `scripts/train/requirements_train.txt`

```
transformers>=4.36.0
datasets>=2.14.0
torch>=2.0.0
evaluate>=0.4.0
seqeval>=1.2.2
accelerate>=0.25.0
```

---

## 6. Lecciones Aprendidas

### 6.1 Error ISS-001: Tokenización Inadecuada

**Causa raíz:** Asumir que la tokenización por espacios era suficiente para NER con modelos transformer.

**Impacto potencial:** Si se hubiera entrenado con el dataset v1:
- F1 degradado estimado: -15% a -25%
- Entidades con puntuación no reconocidas
- Generalización pobre a texto real

**Prevención futura:**
1. Siempre usar el tokenizador del modelo base
2. Implementar auditoría de dataset antes de entrenar
3. Verificar alineación subword-label explícitamente

### 6.2 Importancia de la Investigación Previa

Investigar mejores prácticas ANTES de implementar evitó:
- Hyperparámetros subóptimos (ej: learning_rate=1e-4 causa divergencia)
- Arquitectura incorrecta (ej: sin CRF layer en NER clásico)
- Evaluación errónea (ej: accuracy vs F1 para NER)

### 6.3 Datos Sintéticos: Fortalezas y Limitaciones

**Fortalezas:**
- Control total sobre distribución de entidades
- Cobertura de casos edge (nombres arcaicos, formatos raros)
- Volumen escalable sin coste de anotación

**Limitaciones:**
- Patrones de lenguaje artificiales
- Sin ruido real (OCR errors, typos)
- Requiere validación en datos reales

---

## 7. Trabajo Futuro

### 7.1 Inmediato (Próximos pasos)

1. **Ejecutar entrenamiento:**
   ```bash
   cd ml
   source .venv/bin/activate
   pip install -r scripts/train/requirements_train.txt
   python scripts/train/train_ner.py
   ```

2. **Evaluar por tipo de entidad:**
   - Verificar F1 ≥ 0.85 para cada categoría
   - Identificar entidades problemáticas

3. **Test adversarial:**
   - Nombres arcaicos no vistos
   - Formatos de fecha ambiguos
   - Direcciones incompletas

### 7.2 Mejoras Potenciales

| Mejora | Prioridad | Impacto Esperado |
|--------|-----------|------------------|
| CRF layer | Alta | +4-13% F1 |
| Datos reales anotados | Alta | Mejor generalización |
| Data augmentation | Media | +2-5% F1 |
| Ensemble con regex | Media | +3-5% recall |
| Active learning | Baja | Reducción coste anotación |

### 7.3 Recursos Opcionales

Papers académicos pendientes de evaluar:
- MAPA Project (aclanthology.org/2022.lrec-1.400/) - Legal PII anotado
- 3CEL Contracts (arxiv.org/abs/2501.15990) - Cláusulas contratos
- IMPACT-es Corpus (arxiv.org/pdf/1306.3692.pdf) - Nombres históricos

---

## 8. Estructura del Proyecto

```
ml/
├── data/
│   ├── raw/
│   │   ├── conll2002/              # Corpus NER estándar
│   │   ├── gazetteers_ine/         # Excel INE originales
│   │   ├── municipios/             # Municipios 2024
│   │   ├── codigos_postales/       # CPs España
│   │   └── ai4privacy/             # Dataset transfer learning
│   └── processed/
│       ├── gazetteers/             # JSON procesados
│       ├── synthetic_sentences/     # Oraciones v1 (descartado)
│       └── ner_dataset_v2/         # Dataset final HuggingFace
├── models/
│   ├── checkpoints/                # Modelo base RoBERTa-BNE
│   └── legal_ner_v1/               # Output entrenamiento (pendiente)
├── scripts/
│   ├── preprocess/
│   │   ├── parse_ine_gazetteers.py
│   │   ├── generate_archaic_names.py
│   │   ├── generate_textual_dates.py
│   │   ├── generate_administrative_ids.py
│   │   ├── generate_addresses.py
│   │   ├── generate_organizations.py
│   │   ├── generate_ner_dataset_v2.py
│   │   └── audit_dataset.py
│   └── train/
│       ├── train_ner.py
│       └── requirements_train.txt
└── docs/
    ├── checklists/
    │   └── 2026-02-02_descargas_fase1.md
    └── reports/
        └── 2026-01-15_estado_proyecto_ner.md  # Este documento
```

---

## 9. Conclusiones

1. **Preparación completada:** Gazetteers, dataset v2, y script de entrenamiento listos.

2. **Error crítico evitado:** La auditoría del dataset v1 identificó problemas que habrían degradado el modelo significativamente.

3. **Mejores prácticas aplicadas:** Hyperparámetros basados en investigación, no en suposiciones.

4. **Próximo hito:** Ejecutar entrenamiento y evaluar F1 por entidad.

---

---

## 10. Referencias

### Modelos y Datasets

1. **RoBERTa-BNE-capitel-ner** - PlanTL-GOB-ES
   - https://huggingface.co/PlanTL-GOB-ES/roberta-base-bne-capitel-ner
   - F1 88.5% en CAPITEL

2. **CoNLL-2002 Spanish** - Corpus NER estándar
   - https://www.clips.uantwerpen.be/conll2002/ner/

3. **ai4privacy/pii-masking-300k** - Dataset PII inglés
   - https://huggingface.co/datasets/ai4privacy/pii-masking-300k

### Datos Oficiales INE

4. **Nombres por frecuencia** - INE
   - https://www.ine.es/daco/daco42/nombyam/nombres_por_edad.xls

5. **Apellidos por frecuencia** - INE
   - https://www.ine.es/daco/daco42/nombyam/apellidos_frecuencia.xls

6. **Municipios España 2024** - INE
   - https://www.ine.es/daco/daco42/codmun/

### Papers y Documentación

7. **RoBERTa: A Robustly Optimized BERT Pretraining Approach** - Liu et al., 2019
   - https://arxiv.org/abs/1907.11692
   - Referencia para warmup ratio 6%

8. **HuggingFace Token Classification Guide**
   - https://huggingface.co/docs/transformers/tasks/token_classification
   - Guía de alineación subword-label

9. **seqeval: A Python framework for sequence labeling evaluation**
   - https://github.com/chakki-works/seqeval
   - Métricas entity-level para NER

### Papers Pendientes de Evaluar

10. **MAPA Project** - Legal PII anotado
    - https://aclanthology.org/2022.lrec-1.400/

11. **3CEL Contracts** - Cláusulas contratos
    - https://arxiv.org/abs/2501.15990

12. **IMPACT-es Corpus** - Nombres históricos
    - https://arxiv.org/pdf/1306.3692.pdf

---

**Última actualización:** 2026-02-03
**Próxima revisión:** Post-entrenamiento
