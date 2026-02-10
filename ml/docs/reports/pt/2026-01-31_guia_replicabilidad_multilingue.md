# Guia de Replicabilidade: Pipeline NER-PII Multilíngue

**Data:** 31-01-2026
**Autor:** AlexAlves87
**Projeto:** ContextSafe ML - Expansão Multilíngue
**Versão:** 1.0.0

---

## 1. Resumo Executivo

Este documento descreve como replicar o pipeline híbrido NER-PII da ContextSafe (legal espanhol, F1 0.788) para outros idiomas europeus. A abordagem é **modular**: cada componente é adaptado ao idioma alvo, mantendo a arquitetura comprovada.

### Lição Aprendida (Experimento LoRA)

| Abordagem | F1 Adversarial | Veredito |
|-----------|----------------|----------|
| Fine-tuning LoRA puro | 0.016 | ❌ Overfitting severo |
| Pipeline híbrido (5 elementos) | **0.788** | ✅ Generaliza bem |

> **Conclusão:** O fine-tuning de transformers sem o pipeline híbrido não generaliza para casos adversariais. Os 5 elementos de pós-processamento são **essenciais**.

---

## 2. Arquitetura do Pipeline (Agnóstica ao Idioma)

```
┌─────────────────────────────────────────────────────────────────┐
│                     PIPELINE HÍBRIDO NER-PII                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Texto de entrada                                                │
│       ↓                                                          │
│  ┌────────────────────────────────────────┐                      │
│  │ [1] TextNormalizer                     │ ← Agnóstico ao Idioma│
│  │     - Unicode NFKC                     │                      │
│  │     - Homóglifos (Cirílico→Latino)     │                      │
│  │     - Remoção de largura zero          │                      │
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
│  │     - Algoritmos de verificação        │                      │
│  │     - Ajuste de confiança              │                      │
│  └────────────────────────────────────────┘                      │
│       ↓                                                          │
│  ┌────────────────────────────────────────┐                      │
│  │ [3] Regex Patterns                     │ ← ADAPTAR POR PAÍS   │
│  │     - IDs Nacionais                    │                      │
│  │     - Formatos com espaços/hifens      │                      │
│  └────────────────────────────────────────┘                      │
│       ↓                                                          │
│  ┌────────────────────────────────────────┐                      │
│  │ [4] Date Patterns                      │ ← ADAPTAR POR IDIOMA │
│  │     - Meses no idioma local            │                      │
│  │     - Formatos legais/notariais        │                      │
│  └────────────────────────────────────────┘                      │
│       ↓                                                          │
│  ┌────────────────────────────────────────┐                      │
│  │ [5] Boundary Refinement                │ ← ADAPTAR POR IDIOMA │
│  │     - Prefixos honoríficos             │                      │
│  │     - Sufixos de organização           │                      │
│  └────────────────────────────────────────┘                      │
│       ↓                                                          │
│  Entidades finais                                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Componentes por Tipo de Adaptação

| Componente | Adaptação | Esforço |
|------------|-----------|---------|
| TextNormalizer | Nenhuma (universal) | 0 |
| Transformer NER | Mudar modelo base | Baixo |
| Checksum Validators | Algoritmos por país | Médio |
| Regex Patterns | Padrões por país | Alto |
| Date Patterns | Meses/formatos por idioma | Médio |
| Boundary Refinement | Prefixos/sufixos por idioma | Médio |

---

## 3. Modelos Base Recomendados por Idioma

### 3.1 Modelos Monolíngues (Máximo Desempenho)

| Idioma | Modelo | HuggingFace | Params | Corpus |
|--------|--------|-------------|--------|--------|
| 🇪🇸 Espanhol | RoBERTa-BNE CAPITEL NER | `PlanTL-GOB-ES/roberta-base-bne-capitel-ner` | 125M | BNE + CAPITEL NER |
| 🇬🇧 Inglês | Legal-BERT | `nlpaueb/legal-bert-base-uncased` | 110M | 12GB legal |
| 🇫🇷 Francês | JuriBERT | `dascim/juribert-base` | 110M | Légifrance |
| 🇮🇹 Italiano | Italian-Legal-BERT | `dlicari/Italian-Legal-BERT` | 110M | Giurisprudenza |
| 🇵🇹 Português | Legal-BERTimbau | `rufimelo/Legal-BERTimbau-base` | 110M | 30K docs |
| 🇩🇪 Alemão | German-Legal-BERT | `elenanereiss/bert-german-legal` | 110M | Bundesrecht |

### 3.2 Modelo Multilíngue (Implantação Rápida)

| Modelo | HuggingFace | Params | Idiomas |
|--------|-------------|--------|---------|
| Legal-XLM-RoBERTa | `joelniklaus/legal-xlm-roberta-large` | 355M | 24 idiomas |

**Trade-off:**
- Monolíngue: +2-5% F1, requer modelo por idioma
- Multilíngue: Um único modelo, desempenho ligeiramente inferior

---

## 4. Adaptações por País

### 4.1 Espanha (Implementado ✅)

#### Identificadores Nacionais

| Tipo | Formato | Checksum | Regex |
|------|---------|----------|-------|
| DNI | 8 dígitos + letra | mod 23 | `\d{8}[A-Z]` |
| NIE | X/Y/Z + 7 dígitos + letra | mod 23 | `[XYZ]\d{7}[A-Z]` |
| CIF | Letra + 7 dígitos + contr. | soma par/ímpar | `[A-W]\d{7}[0-9A-J]` |
| IBAN | ES + 22 caracteres | ISO 13616 mod 97 | `ES\d{2}[\d\s]{20}` |
| NSS | 12 dígitos | mod 97 | `\d{12}` |
| Matrícula | 4 dígitos + 3 letras | nenhum | `\d{4}[BCDFGHJKLMNPRSTVWXYZ]{3}` |

#### Prefixos Honoríficos

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

### 4.2 França 🇫🇷

#### Identificadores Nacionais

| Tipo | Formato | Checksum | Regex |
|------|---------|----------|-------|
| NIR (Sécu) | 15 dígitos | mod 97 | `[12]\d{2}(0[1-9]|1[0-2])\d{2}\d{3}\d{3}\d{2}` |
| SIRET | 14 dígitos | Luhn | `\d{14}` |
| SIREN | 9 dígitos | Luhn | `\d{9}` |
| IBAN | FR + 25 caracteres | ISO 13616 | `FR\d{2}[\d\s]{23}` |
| Carte ID | 12 caracteres | nenhum | `[A-Z0-9]{12}` |

#### Prefixos Honoríficos

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

#### Sufixos de Organização

```python
ORG_SUFFIXES_FR = [
    "S.A.", "SA", "S.A.S.", "SAS", "S.A.R.L.", "SARL",
    "S.C.I.", "SCI", "E.U.R.L.", "EURL", "S.N.C.", "SNC",
]
```

---

### 4.3 Itália 🇮🇹

#### Identificadores Nacionais

| Tipo | Formato | Checksum | Regex |
|------|---------|----------|-------|
| Codice Fiscale | 16 caracteres | mod 26 especial | `[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]` |
| Partita IVA | 11 dígitos | Luhn variante | `\d{11}` |
| IBAN | IT + 25 caracteres | ISO 13616 | `IT\d{2}[A-Z][\d\s]{22}` |
| Carta Identità | 2 letras + 7 dígitos | nenhum | `[A-Z]{2}\d{7}` |

#### Checksum Codice Fiscale

```python
def validate_codice_fiscale(cf: str) -> bool:
    """Algoritmo mod 26 com valores especiais para posições pares/ímpares."""
    ODD_VALUES = {'0': 1, '1': 0, '2': 5, ...}  # Tabela completa
    EVEN_VALUES = {'0': 0, '1': 1, '2': 2, ...}
    # Soma posições ímpares com ODD_VALUES, pares com EVEN_VALUES
    # Letra de controle = chr(ord('A') + total % 26)
```

#### Prefixos Honoríficos

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

#### Identificadores Nacionais

| Tipo | Formato | Checksum | Regex |
|------|---------|----------|-------|
| NIF | 9 dígitos | mod 11 | `[123568]\d{8}` |
| CC (Cartão Cidadão) | 8 dígitos + 1 letra + 2 dígitos | mod 11 + letra | `\d{8}[A-Z]\d{2}` |
| NISS | 11 dígitos | mod 10 | `\d{11}` |
| IBAN | PT + 23 caracteres | ISO 13616 | `PT\d{2}[\d\s]{21}` |

#### Checksum NIF Portugal

```python
def validate_nif_pt(nif: str) -> bool:
    """Algoritmo mod 11 com pesos decrescentes."""
    weights = [9, 8, 7, 6, 5, 4, 3, 2]
    total = sum(int(d) * w for d, w in zip(nif[:8], weights))
    control = 11 - (total % 11)
    if control >= 10:
        control = 0
    return int(nif[8]) == control
```

#### Prefixos Honoríficos

```python
PREFIXES_PT = [
    "Senhor", "Senhora", "Sr.", "Sra.", "Srª",
    "Dom", "Dona", "D.",
    "Doutor", "Doutora", "Dr.", "Dra.",
    "Exmo.", "Exma.",
]
```

---

### 4.5 Alemanha 🇩🇪

#### Identificadores Nacionais

| Tipo | Formato | Checksum | Regex |
|------|---------|----------|-------|
| Steuer-ID | 11 dígitos | ISO 7064 mod 11-10 | `\d{11}` |
| Personalausweis | 10 caracteres | mod 10 especial | `[A-Z0-9]{10}` |
| IBAN | DE + 20 caracteres | ISO 13616 | `DE\d{2}[\d\s]{18}` |
| Handelsregister | HRA/HRB + número | nenhum | `HR[AB]\s?\d+` |

#### Prefixos Honoríficos

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

#### Identificadores Nacionais

| Tipo | Formato | Checksum | Regex |
|------|---------|----------|-------|
| NI Number | 2 letras + 6 dígitos + letra | nenhum verificável | `[A-Z]{2}\d{6}[A-D]` |
| Company Number | 8 caracteres | nenhum | `[A-Z]{2}\d{6}|[\d]{8}` |
| IBAN | GB + 22 caracteres | ISO 13616 | `GB\d{2}[A-Z]{4}[\d\s]{14}` |
| Passaporte | 9 dígitos | nenhum | `\d{9}` |

#### Prefixos Honoríficos

```python
PREFIXES_EN = [
    "Mr", "Mr.", "Mrs", "Mrs.", "Ms", "Ms.", "Miss",
    "Dr", "Dr.", "Prof", "Prof.",
    "Sir", "Dame", "Lord", "Lady",
    "The Honourable", "Hon.",
]
```

---

## 5. Checklist de Implementação por Idioma

### Fase 1: Preparação (1-2 dias)

- [ ] **Selecionar modelo base** da tabela 3.1
- [ ] **Baixar modelo** para `models/pretrained/{modelo}/`
- [ ] **Verificar carregamento** com script de teste
- [ ] **Definir categorias PII** relevantes para o país

### Fase 2: Checksum Validators (2-3 dias)

- [ ] **Pesquisar algoritmos de validação** do país
- [ ] **Implementar validadores** em `scripts/preprocess/{country}_validators.py`
- [ ] **Criar testes unitários** (mínimo 20 casos por tipo)
- [ ] **Documentar algoritmos** com referências oficiais

### Fase 3: Regex Patterns (3-5 dias)

- [ ] **Coletar formatos oficiais** de IDs do país
- [ ] **Implementar padrões** em `scripts/preprocess/{country}_id_patterns.py`
- [ ] **Incluir variantes** com espaços, hifens, pontos
- [ ] **Testes com exemplos reais** (anonimizados)

### Fase 4: Date Patterns (1-2 dias)

- [ ] **Traduzir meses** para o idioma alvo
- [ ] **Adaptar formatos** locais legais/notariais
- [ ] **Implementar** em `scripts/preprocess/{country}_date_patterns.py`
- [ ] **Testes com datas reais** de documentos legais

### Fase 5: Boundary Refinement (1-2 dias)

- [ ] **Compilar lista** de prefixos honoríficos
- [ ] **Compilar lista** de sufixos de organização
- [ ] **Implementar** em `scripts/preprocess/{country}_boundary_refinement.py`
- [ ] **Testes com nomes/orgs** reais

### Fase 6: Gazetteers (2-4 dias)

- [ ] **Nomes Próprios** frequentes (equivalente INE)
- [ ] **Sobrenomes** frequentes
- [ ] **Municípios/Cidades**
- [ ] **Organizações** conhecidas (empresas, instituições)

### Fase 7: Test Set Adversarial (2-3 dias)

- [ ] **Criar 30-40 casos** específicos para o idioma:
  - Casos de borda (formatos incomuns)
  - Adversarial (negações, exemplos, ficção)
  - Corrupção OCR
  - Evasão Unicode (já coberto)
  - Mundo real (documentos legais típicos)
- [ ] **Definir entidades esperadas** para cada caso
- [ ] **Executar avaliação SemEval**

### Fase 8: Integração (1-2 dias)

- [ ] **Integrar componentes** em `ner_predictor_{lang}.py`
- [ ] **Executar test set adversarial**
- [ ] **Ajustar** até F1 ≥ 0.70
- [ ] **Documentar resultados**

---

## 6. Estimativa de Esforço Total

| Idioma | Modelo | Complexidade IDs | Esforço Est. |
|--------|--------|------------------|--------------|
| 🇫🇷 Francês | JuriBERT | Média (NIR, SIRET) | 2-3 semanas |
| 🇮🇹 Italiano | Italian-Legal-BERT | Alta (Codice Fiscale) | 3-4 semanas |
| 🇵🇹 Português | Legal-BERTimbau | Média (NIF, CC) | 2-3 semanas |
| 🇩🇪 Alemão | German-Legal-BERT | Média (Steuer-ID) | 2-3 semanas |
| 🇬🇧 Inglês | Legal-BERT | Baixa (NI Number) | 1-2 semanas |

**Total para 5 idiomas:** 10-15 semanas (1 desenvolvedor)
**Com paralelização (2-3 devs):** 4-6 semanas

---

## 7. Estrutura de Arquivos por Idioma

```
ml/
├── scripts/
│   ├── preprocess/
│   │   ├── spanish_id_patterns.py      # ✅ Implementado
│   │   ├── spanish_date_patterns.py    # ✅ Implementado
│   │   ├── boundary_refinement.py      # ✅ Implementado (adaptar)
│   │   │
│   │   ├── french_id_patterns.py       # A implementar
│   │   ├── french_date_patterns.py
│   │   ├── french_validators.py
│   │   │
│   │   ├── italian_id_patterns.py      # A implementar
│   │   ├── italian_date_patterns.py
│   │   ├── italian_validators.py
│   │   │
│   │   └── ... (por idioma)
│   │
│   ├── inference/
│   │   ├── ner_predictor.py            # ✅ Espanhol
│   │   ├── ner_predictor_fr.py         # A implementar
│   │   ├── ner_predictor_it.py
│   │   └── ...
│   │
│   └── evaluate/
│       ├── test_ner_predictor_adversarial_v2.py  # ✅ Espanhol
│       ├── adversarial_tests_fr.py               # A implementar
│       └── ...
│
├── gazetteers/
│   ├── es/                             # ✅ Implementado
│   │   ├── nombres.json
│   │   ├── apellidos.json
│   │   └── municipios.json
│   │
│   ├── fr/                             # A implementar
│   ├── it/
│   ├── pt/
│   ├── de/
│   └── en/
│
└── models/
    └── pretrained/
        ├── legal-xlm-roberta-base/     # ✅ Baixado
        ├── juribert-base/              # A baixar
        ├── italian-legal-bert/
        └── ...
```

---

## 8. Referências

### 8.1 Papers e Documentação

| Recurso | URL | Uso |
|---------|-----|-----|
| Legal-BERT Paper | aclanthology.org/2020.findings-emnlp.261 | Arquitetura |
| JuriBERT Paper | aclanthology.org/2021.nllp-1.9 | Francês legal |
| SemEval 2013 Task 9 | aclweb.org/anthology/S13-2013 | Métricas de avaliação |
| ISO 13616 (IBAN) | iso.org/standard/81090.html | Checksum IBAN |

### 8.2 Fontes de Gazetteers por País

| País | Nomes | Municípios | IDs |
|------|-------|------------|-----|
| 🇪🇸 Espanha | INE | INE | BOE |
| 🇫🇷 França | INSEE | INSEE | Légifrance |
| 🇮🇹 Itália | ISTAT | ISTAT | Normattiva |
| 🇵🇹 Portugal | INE-PT | INE-PT | DRE |
| 🇩🇪 Alemanha | Statistisches Bundesamt | - | Bundesrecht |
| 🇬🇧 Reino Unido | ONS | ONS | legislation.gov.uk |

---

## 9. Lições Aprendidas (ContextSafe ES)

### 9.1 O que funcionou

1.  **Pipeline híbrido > ML puro**: Transformers sozinhos não generalizam para casos adversariais
2.  **Regex para formatos variáveis**: DNI com espaços, IBAN com grupos
3.  **Validação de checksum**: Reduz falsos positivos significativamente
4.  **Refinamento de limites**: Converte PAR→COR (16 casos corrigidos)
5.  **Test set adversarial**: Detecta problemas antes da produção

### 9.2 O que NÃO funcionou

1.  **Fine-tuning LoRA sem pipeline**: 0.016 F1 em adversarial (overfitting)
2.  **GLiNER zero-shot**: 0.325 F1 (não conhece formatos espanhóis)
3.  **Confiar apenas nas métricas do dev set**: 0.989 dev vs 0.016 adversarial

### 9.3 Recomendações

1.  **Sempre criar test set adversarial** antes de declarar "pronto"
2.  **Implementar validadores de checksum** para todos os IDs com verificação matemática
3.  **Investir em gazetteers de qualidade** (nomes, municípios)
4.  **Documentar cada elemento** com testes independentes

---

## 10. Próximos Passos

1.  **Priorizar idioma** de acordo com a demanda do mercado
2.  **Baixar modelo base** do idioma selecionado
3.  **Adaptar componentes** seguindo este checklist
4.  **Criar test set adversarial** específico
5.  **Iterar até F1 ≥ 0.70** em adversarial

---

**Gerado por:** AlexAlves87
**Data:** 31-01-2026
**Versão:** 1.0.0
