# Relatório de Estado: Sistema NER-PII para Documentos Legais Espanhóis

**Data:** 15-01-2026
**Versão:** 1.0
**Autor:** AlexAlves87
**Projeto:** ContextSafe ML - Fine-tuning NER

---

## Resumo Executivo

Este relatório documenta o desenvolvimento do sistema de deteção de PII (Personally Identifiable Information) para documentos legais espanhóis. O sistema deve detetar 13 categorias de entidades com F1 ≥ 0.85.

### Estado Atual

| Fase | Estado | Progresso |
|------|--------|-----------|
| Descarregamento de dados base | Concluído | 100% |
| Geração de gazetteers | Concluído | 100% |
| Dataset sintético v1 | Descartado | Erro crítico |
| Dataset sintético v2 | Concluído | 100% |
| Script de treino | Concluído | 100% |
| Treino do modelo | Pendente | 0% |

---

## 1. Objetivo do Projeto

Desenvolver um modelo NER especializado em documentos legais espanhóis (testamentos, sentenças, escrituras, contratos) capaz de detetar:

| Categoria | Exemplos | Prioridade |
|-----------|----------|------------|
| PERSON | Hermógenes Pérez García | Alta |
| DATE | 15 de marzo de 2024 | Alta |
| DNI_NIE | 12345678Z, X1234567A | Alta |
| IBAN | ES9121000418450200051332 | Alta |
| NSS | 281234567890 | Média |
| PHONE | 612 345 678 | Média |
| ADDRESS | Calle Mayor 15, 3º B | Alta |
| POSTAL_CODE | 28001 | Média |
| ORGANIZATION | Banco Santander, S.A. | Alta |
| LOCATION | Madrid, Comunidad de Madrid | Média |
| ECLI | ECLI:ES:TS:2024:1234 | Baixa |
| LICENSE_PLATE | 1234 ABC | Baixa |
| CADASTRAL_REF | 1234567AB1234S0001AB | Baixa |
| PROFESSIONAL_ID | Colegiado nº 12345 | Baixa |

---

## 2. Dados Descarregados

### 2.1 Fontes Oficiais

| Recurso | Localização | Tamanho | Descrição |
|---------|-------------|---------|-------------|
| CoNLL-2002 Espanhol | `data/raw/conll2002/` | 4.0 MB | Corpus NER padrão |
| INE Nomes por década | `data/raw/gazetteers_ine/nombres_por_fecha.xls` | 1.1 MB | Frequência temporal |
| INE Nomes frequentes | `data/raw/gazetteers_ine/nombres_mas_frecuentes.xls` | 278 KB | Top nomes |
| INE Apelidos | `data/raw/gazetteers_ine/apellidos_frecuencia.xls` | 12 MB | 27,251 apelidos |
| INE Municípios 2024 | `data/raw/municipios/municipios_2024.xlsx` | 300 KB | 8,115 municípios |
| Códigos postais | `data/raw/codigos_postales/codigos_postales.csv` | 359 KB | 11,051 CPs |
| ai4privacy/pii-masking-300k | `data/raw/ai4privacy/` | ~100 MB | Transfer learning |

### 2.2 Modelo Base

| Modelo | Localização | Tamanho | F1 Base |
|--------|-------------|---------|---------|
| roberta-base-bne-capitel-ner | `models/checkpoints/` | ~500 MB | 88.5% (CAPITEL) |

**Decisão de modelo:** O MEL (Modelo Espanhol Legal) foi avaliado mas carece de fine-tuning NER. O RoBERTa-BNE-capitel-ner foi selecionado pela sua especialização em NER espanhol.

---

## 3. Gazetteers Gerados

### 3.1 Scripts de Geração

| Script | Função | Output |
|--------|--------|--------|
| `parse_ine_gazetteers.py` | Faz parse de Excel INE → JSON | apellidos.json, nombres_*.json |
| `generate_archaic_names.py` | Gera nomes arcaicos legais | nombres_arcaicos.json |
| `generate_textual_dates.py` | Datas em formato legal | fechas_textuales.json |
| `generate_administrative_ids.py` | DNI, NIE, IBAN, NSS com checksums inválidos | identificadores_administrativos.json |
| `generate_addresses.py` | Moradas espanholas completas | direcciones.json |
| `generate_organizations.py` | Empresas, tribunais, bancos | organizaciones.json |

### 3.2 Ficheiros Gerados

| Ficheiro | Tamanho | Conteúdo |
|----------|---------|----------|
| `apellidos.json` | 1.8 MB | 27,251 apelidos com frequências INE |
| `codigos_postales.json` | 1.2 MB | 11,051 códigos postais |
| `municipios.json` | 164 KB | 8,115 municípios espanhóis |
| `nombres_hombres.json` | 40 KB | 550 nomes masculinos por década |
| `nombres_mujeres.json` | 41 KB | 550 nomes femininos por década |
| `nombres_todos.json` | 3.9 KB | 260 nomes únicos (INE) |
| `nombres_arcaicos.json` | 138 KB | 940 nomes arcaicos + 5,070 combinações |
| `nombres_arcaicos_flat.json` | 267 KB | Lista plana para NER |
| `fechas_textuales.json` | 159 KB | 645 datas com 41 padrões legais |
| `fechas_textuales_flat.json` | 86 KB | Lista plana |
| `identificadores_administrativos.json` | 482 KB | 2,550 IDs sintéticos |
| `identificadores_administrativos_flat.json` | 134 KB | Lista plana |
| `direcciones.json` | 159 KB | 600 moradas + 416 com contexto legal |
| `direcciones_flat.json` | 59 KB | Lista plana |
| `organizaciones.json` | 185 KB | 1,000 organizações |
| `organizaciones_flat.json` | 75 KB | Lista plana |

**Total gazetteers:** ~4.9 MB

### 3.3 Características Especiais

**Nomes Arcaicos:** Inclui nomes frequentes em documentos legais históricos:
- Hermógenes, Segismundo, Práxedes, Gertrudis, Baldomero, Saturnino, Patrocinio...
- Combinações compostas: María del Carmen, José Antonio, Juan de Dios...

**Identificadores Administrativos:** Gerados com checksums MATEMATICAMENTE INVÁLIDOS:
- DNI: Letra de controlo incorreta (mod-23 incorreto)
- NIE: Prefixo X/Y/Z com letra incorreta
- IBAN: Dígitos de controlo "00" (sempre inválido)
- NSS: Dígitos de controlo incorretos (mod-97)

Isto garante que nenhum identificador sintético corresponda a dados reais.

---

## 4. Dataset Sintético

### 4.1 Dataset v1 - ERRO CRÍTICO (DESCARTADO)

**Data:** 15-01-2026

O primeiro dataset gerado continha erros críticos que teriam degradado significativamente o modelo.

#### Erro 1: Pontuação Colada aos Tokens

**Problema:** A tokenização simples por espaços em branco causava que a pontuação ficasse colada às entidades.

**Exemplo do erro:**
```
Texto: "Don Hermógenes Freijanes, con DNI 73364386X."
Tokens: ["Don", "Hermógenes", "Freijanes,", "con", "DNI", "73364386X."]
Labels: ["O",   "B-PERSON",   "I-PERSON",   "O",   "O",   "B-DNI_NIE"]
```

**Impacto:** O modelo aprenderia que "Freijanes," (com vírgula) é uma pessoa, mas durante a inferência não reconheceria "Freijanes" sem vírgula.

**Estatísticas do erro:**
- 6,806 tokens com pontuação colada
- Afetava principalmente: PERSON, DNI_NIE, IBAN, PHONE
- ~30% das entidades comprometidas

#### Erro 2: Sem Alinhamento de Subwords

**Problema:** As etiquetas BIO estavam ao nível da palavra, mas o BERT usa tokenização de subwords.

**Exemplo do erro:**
```
Palavra: "Hermógenes"
Subwords: ["Her", "##mó", "##genes"]
Label v1: Apenas uma etiqueta para toda a palavra → qual subword a recebe?
```

**Impacto:** Sem alinhamento explícito, o modelo não poderia aprender corretamente a relação entre subwords e etiquetas.

#### Erro 3: Desequilíbrio de Entidades

| Entidade | Percentagem v1 | Problema |
|----------|----------------|----------|
| PERSON | 30.3% | Sobrerepresentado |
| ADDRESS | 12.6% | OK |
| DNI_NIE | 10.1% | OK |
| NSS | 1.7% | Sub-representado |
| ECLI | 1.7% | Sub-representado |
| LICENSE_PLATE | 1.7% | Sub-representado |

### 4.2 Dataset v2 - CORRIGIDO

**Data:** 15-01-2026

**Script:** `scripts/preprocess/generate_ner_dataset_v2.py`

#### Correções Implementadas

**1. Tokenização com HuggingFace:**
```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("PlanTL-GOB-ES/roberta-base-bne")

# A tokenização separa automaticamente a pontuação
# "Freijanes," → ["Fre", "##ij", "##anes", ","]
```

**2. Alinhamento com word_ids():**
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
            labels.append(entity_label)  # Primeiro subword
        else:
            labels.append(-100)  # Continuação
```

**3. Templates Balanceados:**
- Adicionados 50+ templates específicos para entidades minoritárias
- Aumentada frequência de NSS, ECLI, LICENSE_PLATE, CADASTRAL_REF

#### Estatísticas v2

| Split | Amostras | Tokens Totais |
|-------|----------|---------------|
| Train | 4,925 | ~630,000 |
| Validation | 818 | ~105,000 |
| Test | 818 | ~105,000 |
| **Total** | **6,561** | **~840,000** |

**Distribuição de entidades v2:**

| Entidade | Contagem | % |
|----------|----------|---|
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

#### Formato de Saída

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

**Esquema de dados:**
```python
{
    "input_ids": [0, 1234, 5678, ...],      # IDs de Token
    "attention_mask": [1, 1, 1, ...],        # Máscara de atenção
    "labels": [-100, 1, 2, -100, ...],       # Etiquetas alinhadas
}
```

**Etiquetas (29 classes):**
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

## 5. Configuração de Treino

### 5.1 Investigação de Melhores Práticas

Foram investigadas as melhores práticas para fine-tuning de NER com base em:
- Documentação HuggingFace
- Papers académicos (RoBERTa, BERT para NER)
- Benchmarks de modelos espanhóis (CAPITEL, AnCora)

### 5.2 Hiperparâmetros Selecionados

**Ficheiro:** `scripts/train/train_ner.py`

```python
CONFIG = {
    # Otimização (MAIS IMPORTANTE)
    "learning_rate": 2e-5,          # Grelha: {1e-5, 2e-5, 3e-5, 5e-5}
    "weight_decay": 0.01,           # Regularização L2
    "adam_epsilon": 1e-8,           # Estabilidade numérica

    # Batching
    "per_device_train_batch_size": 16,
    "per_device_eval_batch_size": 32,
    "gradient_accumulation_steps": 2,  # Batch efetivo = 32

    # Epochs
    "num_train_epochs": 4,          # Conservador para legal

    # Learning Rate Scheduling
    "warmup_ratio": 0.06,           # 6% warmup (paper RoBERTa)
    "lr_scheduler_type": "linear",  # Decaimento linear

    # Early Stopping
    "early_stopping_patience": 2,   # Parar se não melhorar em 2 evals
    "metric_for_best_model": "f1",

    # Comprimento de Sequência
    "max_length": 384,              # Documentos legais podem ser extensos

    # Hardware
    "fp16": True,                   # Precisão mista se GPU
    "dataloader_num_workers": 4,

    # Reprodutibilidade
    "seed": 42,
}
```

### 5.3 Justificação de Decisões

| Parâmetro | Valor | Justificação |
|-----------|-------|--------------|
| learning_rate | 2e-5 | Valor padrão para fine-tuning BERT/RoBERTa |
| batch_size | 32 (efetivo) | Equilíbrio entre estabilidade e memória |
| epochs | 4 | Evitar overfitting em dados sintéticos |
| warmup | 6% | Recomendação paper RoBERTa |
| max_length | 384 | Documentos legais podem ser extensos |
| early_stopping | 2 | Deteção precoce de overfitting |

### 5.4 Dependências

**Ficheiro:** `scripts/train/requirements_train.txt`

```
transformers>=4.36.0
datasets>=2.14.0
torch>=2.0.0
evaluate>=0.4.0
seqeval>=1.2.2
accelerate>=0.25.0
```

---

## 6. Lições Aprendidas

### 6.1 Erro ISS-001: Tokenização Inadequada

**Causa raiz:** Assumir que a tokenização por espaços era suficiente para NER com modelos transformer.

**Impacto potencial:** Se treinado com o dataset v1:
- Degradação F1 estimada: -15% a -25%
- Entidades com pontuação não reconhecidas
- Generalização fraca para texto real

**Prevenção futura:**
1. Usar sempre o tokenizador do modelo base
2. Implementar auditoria de dataset antes de treinar
3. Verificar alinhamento subword-label explicitamente

### 6.2 Importância da Investigação Prévia

Investigar melhores práticas ANTES de implementar evitou:
- Hiperparâmetros subótimos (ex: learning_rate=1e-4 causa divergência)
- Arquitetura incorreta (ex: sem camada CRF em NER clássico)
- Avaliação errónea (ex: accuracy vs F1 para NER)

### 6.3 Dados Sintéticos: Pontos Fortes e Limitações

**Pontos Fortes:**
- Controlo total sobre distribuição de entidades
- Cobertura de casos limite (nomes arcaicos, formatos raros)
- Volume escalável sem custo de anotação

**Limitações:**
- Padrões de linguagem artificiais
- Sem ruído real (erros OCR, gralhas)
- Requer validação em dados reais

---

## 7. Trabalho Futuro

### 7.1 Imediato (Próximos passos)

1. **Executar treino:**
   ```bash
   cd ml
   source .venv/bin/activate
   pip install -r scripts/train/requirements_train.txt
   python scripts/train/train_ner.py
   ```

2. **Avaliar por tipo de entidade:**
   - Verificar F1 ≥ 0.85 para cada categoria
   - Identificar entidades problemáticas

3. **Teste adversarial:**
   - Nomes arcaicos não vistos
   - Formatos de data ambíguos
   - Moradas incompletas

### 7.2 Melhorias Potenciais

| Melhoria | Prioridade | Impacto Esperado |
|----------|------------|------------------|
| Camada CRF | Alta | +4-13% F1 |
| Dados reais anotados | Alta | Melhor generalização |
| Data augmentation | Média | +2-5% F1 |
| Ensemble com regex | Média | +3-5% recall |
| Active learning | Baixa | Redução custo anotação |

### 7.3 Recursos Opcionais

Papers académicos pendentes de avaliar:
- MAPA Project (aclanthology.org/2022.lrec-1.400/) - Legal PII anotado
- 3CEL Contracts (arxiv.org/abs/2501.15990) - Cláusulas contratos
- IMPACT-es Corpus (arxiv.org/pdf/1306.3692.pdf) - Nomes históricos

---

## 8. Estrutura do Projeto

```
ml/
├── data/
│   ├── raw/
│   │   ├── conll2002/              # Corpus NER padrão
│   │   ├── gazetteers_ine/         # Excel INE original
│   │   ├── municipios/             # Municípios 2024
│   │   ├── codigos_postales/       # CPs Espanha
│   │   └── ai4privacy/             # Dataset transfer learning
│   └── processed/
│       ├── gazetteers/             # JSON processados
│       ├── synthetic_sentences/     # Frases v1 (descartado)
│       └── ner_dataset_v2/         # Dataset final HuggingFace
├── models/
│   ├── checkpoints/                # Modelo base RoBERTa-BNE
│   └── legal_ner_v1/               # Output treino (pendente)
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

## 9. Conclusões

1. **Preparação concluída:** Gazetteers, dataset v2, e script de treino prontos.

2. **Erro crítico evitado:** A auditoria do dataset v1 identificou problemas que teriam degradado o modelo significativamente.

3. **Melhores práticas aplicadas:** Hiperparâmetros baseados em investigação, não em suposições.

4. **Próximo marco:** Executar treino e avaliar F1 por entidade.

---

---

## 10. Referências

### Modelos e Datasets

1. **RoBERTa-BNE-capitel-ner** - PlanTL-GOB-ES
   - https://huggingface.co/PlanTL-GOB-ES/roberta-base-bne-capitel-ner
   - F1 88.5% no CAPITEL

2. **CoNLL-2002 Espanhol** - Corpus NER padrão
   - https://www.clips.uantwerpen.be/conll2002/ner/

3. **ai4privacy/pii-masking-300k** - Dataset PII inglês
   - https://huggingface.co/datasets/ai4privacy/pii-masking-300k

### Dados Oficiais INE

4. **Nomes por frequência** - INE
   - https://www.ine.es/daco/daco42/nombyam/nombres_por_edad.xls

5. **Apelidos por frequência** - INE
   - https://www.ine.es/daco/daco42/nombyam/apellidos_frecuencia.xls

6. **Municípios Espanha 2024** - INE
   - https://www.ine.es/daco/daco42/codmun/

### Papers e Documentação

7. **RoBERTa: A Robustly Optimized BERT Pretraining Approach** - Liu et al., 2019
   - https://arxiv.org/abs/1907.11692
   - Referência para 6% warmup ratio

8. **HuggingFace Token Classification Guide**
   - https://huggingface.co/docs/transformers/tasks/token_classification
   - Guia de alinhamento subword-label

9. **seqeval: A Python framework for sequence labeling evaluation**
   - https://github.com/chakki-works/seqeval
   - Métricas entity-level para NER

### Papers Pendentes de Avaliar

10. **MAPA Project** - Legal PII anotado
    - https://aclanthology.org/2022.lrec-1.400/

11. **3CEL Contracts** - Cláusulas contratos
    - https://arxiv.org/abs/2501.15990

12. **IMPACT-es Corpus** - Nomes históricos
    - https://arxiv.org/pdf/1306.3692.pdf

---

**Última atualização:** 03-02-2026
**Próxima revisão:** Pós-treino
