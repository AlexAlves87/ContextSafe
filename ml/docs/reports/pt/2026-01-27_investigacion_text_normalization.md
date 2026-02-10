# Investigação: Normalização de Texto para NER em Documentos Legais

**Data:** 27-01-2026
**Autor:** AlexAlves87
**Tipo:** Revisão de Literatura Académica
**Estado:** Concluído

---

## 1. Resumo Executivo

Esta investigação analisa as melhores práticas para normalização de texto em pipelines NER, com ênfase em:
1. Normalização Unicode (fullwidth, zero-width, homoglyphs)
2. Correção de artefactos OCR
3. Integração com modelos transformer

### Principais Descobertas

| Descoberta | Fonte | Impacto |
|------------|-------|---------|
| NFKC normaliza fullwidth → ASCII automaticamente | UAX #15 Unicode Standard | Alto |
| Carateres zero-width (U+200B-U+200F) devem ser eliminados explicitamente | Unicode Consortium | Alto |
| Neurónios sensíveis a OCR existem em transformers e podem ser modulados | arXiv:2409.16934 (ICADL 2024) | Médio |
| Preprocessing deve coincidir com pretraining do modelo | Best practices 2024 | Crítico |
| NFKC destrói informação em scripts complexos (árabe, hebraico) | UAX #15 | Baixo (não se aplica a espanhol) |

---

## 2. Metodologia

### 2.1 Fontes Consultadas

| Fonte | Tipo | Ano | Relevância |
|-------|------|-----|------------|
| UAX #15 Unicode Standard | Especificação | 2024 | Norma Unicode |
| arXiv:2409.16934 | Paper (ICADL 2024) | 2024 | Neurónios sensíveis a OCR |
| TACL Neural OCR Post-Hoc | Paper académico | 2021 | Correção OCR neural |
| Brenndoerfer NLP Guide | Tutorial técnico | 2024 | Best practices industriais |
| Promptfoo Security | Artigo técnico | 2024 | Evasão Unicode em AI |

### 2.2 Critérios de Pesquisa

- "text normalization NER preprocessing Unicode OCR"
- "Unicode normalization NLP NER fullwidth characters zero-width space"
- "OCR post-correction NER robustness neural network ACL EMNLP"

---

## 3. Resultados

### 3.1 Formas de Normalização Unicode

O padrão Unicode (UAX #15) define 4 formas de normalização:

| Forma | Nome | Descrição | Uso em NER |
|-------|------|-----------|------------|
| **NFC** | Canonical Composition | Compõe carateres (é = e + ´) | Padrão |
| **NFD** | Canonical Decomposition | Decompõe carateres | Pesquisa |
| **NFKC** | Compatibility Composition | NFC + compatibilidade | **Recomendado para NER** |
| **NFKD** | Compatibility Decomposition | NFD + compatibilidade | Análise |

**Fonte:** [UAX #15: Unicode Normalization Forms](https://unicode.org/reports/tr15/)

#### 3.1.1 NFKC para Normalização de Entidades

NFKC é a forma recomendada para NER porque:

```
Fullwidth:  １２３４５６７８ → 12345678
Superscript: ² → 2
Fractions:   ½ → 1/2
Roman:       Ⅳ → IV
Ligatures:   ﬁ → fi
```

**Aviso:** NFKC destrói informação em scripts complexos (árabe, hebraico, devanagari) onde os carateres de controlo são semanticamente relevantes. Para espanhol legal, isto não é um problema.

### 3.2 Carateres Invisíveis Problemáticos

**Fonte:** [The Invisible Threat: Zero-Width Unicode Characters](https://www.promptfoo.dev/blog/invisible-unicode-threats/)

| Codepoint | Nome | Problema | Ação |
|-----------|------|----------|------|
| U+200B | Zero Width Space | Quebra tokenização | Eliminar |
| U+200C | Zero Width Non-Joiner | Separa carateres unidos | Eliminar |
| U+200D | Zero Width Joiner | Une carateres separados | Eliminar |
| U+200E | Left-to-Right Mark | Confunde direção texto | Eliminar |
| U+200F | Right-to-Left Mark | Confunde direção texto | Eliminar |
| U+FEFF | BOM / Zero Width No-Break | Artefacto de encoding | Eliminar |
| U+00A0 | Non-Breaking Space | Não detetado por isspace() | → espaço normal |
| U+00AD | Soft Hyphen | Hífen invisível | Eliminar |

**Impacto em NER:**
- DNI `123​456​78Z` (com U+200B) não corresponde a regex `\d{8}[A-Z]`
- Tokenizador divide palavra em múltiplos tokens
- Modelo não reconhece a entidade

### 3.3 Homoglyphs e Evasão

**Fonte:** [Invisible Unicode Tricks Bypass AI Detection](https://justdone.com/blog/ai/invisible-unicode-tricks)

| Latino | Cirílico | Visual | Código |
|--------|----------|--------|--------|
| A | А | Idêntico | U+0041 vs U+0410 |
| B | В | Idêntico | U+0042 vs U+0412 |
| E | Е | Idêntico | U+0045 vs U+0415 |
| O | О | Idêntico | U+004F vs U+041E |
| X | Х | Idêntico | U+0058 vs U+0425 |

**Impacto em NER:**
- DNI `12345678Х` (Cirílico) não corresponde a regex com `[A-Z]`
- Modelo pode não reconhecer como DNI válido

**Solução:** Normalizar homoglyphs latinos comuns antes de NER.

### 3.4 Neurónios Sensíveis a OCR em Transformers

**Fonte:** [Investigating OCR-Sensitive Neurons](https://arxiv.org/abs/2409.16934) (ICADL 2024)

#### Descobertas do Paper

1. **Os transformers têm neurónios sensíveis a OCR:**
   - Identificados através de análise de padrões de ativação
   - Respondem diferentemente a texto limpo vs corrompido

2. **Camadas críticas identificadas:**
   - Llama 2: Camadas 0-2, 11-13, 23-28
   - Mistral: Camadas 29-31

3. **Solução proposta:**
   - Neutralizar neurónios sensíveis a OCR
   - Melhora desempenho NER em documentos históricos

#### Aplicação a ContextSafe

Para o nosso modelo RoBERTa fine-tuned:
- A normalização de texto ANTES de inferência é mais prática
- Neutralizar neurónios requer modificar arquitetura do modelo
- **Recomendação:** Pré-processamento, não modificação de modelo

### 3.5 Erros OCR Comuns e Normalização

**Fonte:** [OCR Data Entry: Preprocessing Text for NLP](https://labelyourdata.com/articles/ocr-data-entry)

| Erro OCR | Padrão | Normalização |
|----------|--------|--------------|
| l ↔ I ↔ 1 | `DNl`, `DN1` | → `DNI` |
| O ↔ 0 | `2l0O` | Contextual (números) |
| rn ↔ m | `nom` → `nom` | Dicionário |
| S ↔ 5 | `E5123` | Contextual |
| B ↔ 8 | `B-123` vs `8-123` | Contextual |

**Estratégia recomendada:**
1. **Pré-processo simples:** l/I/1 → normalizar segundo contexto
2. **Validação posterior:** Checksums (DNI, IBAN) rejeitam inválidos
3. **Não tentar corrigir tudo:** Melhor rejeitar que inventar

### 3.6 Desajuste Preprocessing-Pretraining

**Fonte:** [Text Preprocessing Guide](https://mbrenndoerfer.com/writing/text-preprocessing-nlp-tokenization-normalization)

> "If you train a model with aggressively preprocessed text but deploy it on minimally preprocessed input, performance will crater."

**Crítico para o nosso modelo:**
- RoBERTa-BNE foi pré-treinado com texto case-sensitive
- NÃO aplicar lowercase
- SIM aplicar normalização Unicode (NFKC)
- SIM eliminar carateres zero-width

---

## 4. Pipeline de Normalização Proposto

### 4.1 Ordem de Operações

```
Texto OCR/Raw
    ↓
[1] Eliminar BOM (U+FEFF)
    ↓
[2] Eliminar zero-width (U+200B-U+200F, U+2060-U+206F)
    ↓
[3] Normalização NFKC (fullwidth → ASCII)
    ↓
[4] Normalizar espaços (U+00A0 → espaço, colapsar múltiplos)
    ↓
[5] Homoglyph mapping (cirílico comum → latino)
    ↓
[6] OCR contextual (DNl → DNI apenas se contexto indicar)
    ↓
Texto Normalizado → NER
```

### 4.2 Implementação Python

```python
import unicodedata
import re

# Carateres a eliminar
ZERO_WIDTH = re.compile(r'[\u200b-\u200f\u2060-\u206f\ufeff]')

# Homoglyphs cirílico → latino
HOMOGLYPHS = {
    '\u0410': 'A',  # А → A
    '\u0412': 'B',  # В → B
    '\u0415': 'E',  # Е → E
    '\u041e': 'O',  # О → O
    '\u0421': 'C',  # С → C
    '\u0425': 'X',  # Х → X
    '\u0430': 'a',  # а → a
    '\u0435': 'e',  # е → e
    '\u043e': 'o',  # о → o
    '\u0441': 'c',  # с → c
    '\u0445': 'x',  # х → x
}

def normalize_text(text: str) -> str:
    """
    Normalize text for NER processing.

    Applies: NFKC, zero-width removal, homoglyph mapping, space normalization.
    Does NOT apply: lowercase (RoBERTa is case-sensitive).
    """
    # 1. Remove BOM and zero-width
    text = ZERO_WIDTH.sub('', text)

    # 2. NFKC normalization (fullwidth → ASCII)
    text = unicodedata.normalize('NFKC', text)

    # 3. Homoglyph mapping
    for cyrillic, latin in HOMOGLYPHS.items():
        text = text.replace(cyrillic, latin)

    # 4. Normalize spaces (NBSP → space, collapse multiples)
    text = text.replace('\u00a0', ' ')
    text = re.sub(r' +', ' ', text)

    # 5. Remove soft hyphens
    text = text.replace('\u00ad', '')

    return text.strip()
```

### 4.3 Testes de Validação

| Input | Output Esperado | Teste |
|-------|-----------------|-------|
| `１２３４５６７８Z` | `12345678Z` | Fullwidth |
| `123​456​78Z` | `12345678Z` | Zero-width |
| `12345678Х` | `12345678X` | Cyrillic X |
| `D N I` | `D N I` | Espaços (sem colapsar palavras) |
| `María` | `María` | Acentos preservados |

---

## 5. Análise de Gaps

### 5.1 Comparação: Prática Atual vs Best Practices

| Aspeto | Best Practice | Implementação Atual | Gap |
|--------|---------------|---------------------|-----|
| NFKC normalization | Aplicar antes de NER | Não implementado | **CRÍTICO** |
| Zero-width removal | Eliminar U+200B-F | Não implementado | **CRÍTICO** |
| Homoglyph mapping | Cirílico → Latino | Não implementado | ALTO |
| Space normalization | NBSP → espaço | Não implementado | MÉDIO |
| OCR contextual | DNl → DNI | Não implementado | MÉDIO |
| Case preservation | NÃO lowercase | Correto | ✓ OK |

### 5.2 Impacto Estimado

| Correção | Esforço | Impacto em Testes |
|----------|---------|-------------------|
| NFKC + zero-width | Baixo (10 linhas) | `fullwidth_numbers`: PASS |
| Homoglyph mapping | Baixo (tabela) | `cyrillic_o`: PASS (já passa, mas mais robusto) |
| Space normalization | Baixo | Reduz FPs em tokenização |
| **Total** | **~50 linhas Python** | **+5-10% pass rate adversarial** |

---

## 6. Conclusões

### 6.1 Principais Descobertas

1. **NFKC é suficiente** para normalizar fullwidth → ASCII sem código adicional
2. **Carateres zero-width** devem ser eliminados explicitamente (regex simples)
3. **Homoglyphs** requerem tabela de mapeamento (Cirílico → Latino)
4. **NÃO aplicar lowercase** - RoBERTa é case-sensitive
5. **OCR contextual** é complexo - melhor validar com checksums depois

### 6.2 Recomendação para ContextSafe

**Implementar `scripts/preprocess/text_normalizer.py`** com:
1. Função `normalize_text()` como descrito acima
2. Integrar em pipeline de inferência ANTES do tokenizador
3. Aplicar também durante geração de dataset de treino

**Prioridade:** ALTA - Resolverá testes `fullwidth_numbers` e melhorará robustez geral.

---

## 7. Referências

### Papers Académicos

1. **Investigating OCR-Sensitive Neurons to Improve Entity Recognition in Historical Documents**
   - arXiv:2409.16934, ICADL 2024
   - URL: https://arxiv.org/abs/2409.16934

2. **Neural OCR Post-Hoc Correction of Historical Corpora**
   - TACL, MIT Press
   - URL: https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00379

### Padrões e Especificações

3. **UAX #15: Unicode Normalization Forms**
   - Unicode Consortium
   - URL: https://unicode.org/reports/tr15/

### Recursos Técnicos

4. **Text Normalization: Unicode Forms, Case Folding & Whitespace Handling for NLP**
   - Michael Brenndoerfer, 2024
   - URL: https://mbrenndoerfer.com/writing/text-normalization-unicode-nlp

5. **The Invisible Threat: How Zero-Width Unicode Characters Can Silently Backdoor Your AI-Generated Code**
   - Promptfoo, 2024
   - URL: https://www.promptfoo.dev/blog/invisible-unicode-threats/

6. **OCR Data Entry: Preprocessing Text for NLP Tasks in 2025**
   - Label Your Data
   - URL: https://labelyourdata.com/articles/ocr-data-entry

7. **Zero-width space - Wikipedia**
   - URL: https://en.wikipedia.org/wiki/Zero-width_space

---

**Tempo de investigação:** 45 min
**Gerado por:** AlexAlves87
**Data:** 27-01-2026
