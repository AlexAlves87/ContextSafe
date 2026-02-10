# Avaliação Adversarial - NER Legal Espanhol

**Data:** 2026-01-20
**Modelo:** legal_ner_v1
**Testes:** 35

---

## Resumo Executivo

| Métrica | Valor |
|---------|-------|
| Testes Totais | 35 |
| Aprovados | 16 (45.7%) |
| Reprovados | 19 (54.3%) |

### Por Categoria

| Categoria | Aprovados | Total | Taxa |
|-----------|---------|-------|------|
| adversarial | 4 | 8 | 50.0% |
| edge_case | 6 | 9 | 66.7% |
| ocr_corruption | 1 | 5 | 20.0% |
| real_world | 3 | 10 | 30.0% |
| unicode_evasion | 2 | 3 | 66.7% |

### Por Dificuldade

| Dificuldade | Aprovados | Total | Taxa |
|------------|---------|-------|------|
| easy | 4 | 4 | 100.0% |
| medium | 6 | 12 | 50.0% |
| hard | 6 | 19 | 31.6% |

---

## Resultados Detalhados

### EDGE CASE

#### single_letter_name [PASS]

**Dificuldade:** medium

**Texto:**
```
El demandante J. García presentó recurso.
```

**Esperado (1):**
- `J. García` → PERSON

**Detectado (1):**
- `J. García` → PERSON

**Resultado:** 1 corretos, 0 perdidos, 0 falsos positivos

**Notas:** Padrão Inicial + Sobrenome

---

#### very_long_name [PASS]

**Dificuldade:** hard

**Texto:**
```
Compareció Don José María de la Santísima Trinidad Fernández-López de Haro y Martínez de Pisón.
```

**Esperado (1):**
- `José María de la Santísima Trinidad Fernández-López de Haro y Martínez de Pisón` → PERSON

**Detectado (1):**
- `Don José María de la Santísima Trinidad Fernández-López de Haro y Martínez de Pisón` → PERSON

**Resultado:** 1 corretos, 0 perdidos, 0 falsos positivos

**Notas:** Nome nobre composto com partículas

---

#### dni_without_letter [PASS]

**Dificuldade:** medium

**Texto:**
```
DNI número 12345678 (pendiente de verificación).
```

**Esperado (1):**
- `12345678` → DNI_NIE

**Detectado (1):**
- `12345678` → DNI_NIE

**Resultado:** 1 corretos, 0 perdidos, 0 falsos positivos

**Notas:** DNI sem letra de controle

---

#### dni_with_spaces [FAIL]

**Dificuldade:** hard

**Texto:**
```
Su documento de identidad es 12 345 678 Z.
```

**Esperado (1):**
- `12 345 678 Z` → DNI_NIE

**Detectado (2):**
- `12` → CADASTRAL_REF
- `345 678 Z` → NSS

**Resultado:** 0 corretos, 1 perdidos, 2 falsos positivos

**Notas:** DNI com espaços internos

---

#### iban_with_spaces [PASS]

**Dificuldade:** easy

**Texto:**
```
Transferir a ES91 2100 0418 4502 0005 1332.
```

**Esperado (1):**
- `ES91 2100 0418 4502 0005 1332` → IBAN

**Detectado (2):**
- `ES91 21` → IBAN
- `00 0418 4502 0005 1332` → CADASTRAL_REF

**Resultado:** 1 corretos, 0 perdidos, 1 falsos positivos

**Notas:** Formato IBAN padrão com espaços

---

#### phone_international [FAIL]

**Dificuldade:** medium

**Texto:**
```
Contacto: +34 612 345 678 o 0034612345678.
```

**Esperado (2):**
- `+34 612 345 678` → PHONE
- `0034612345678` → PHONE

**Detectado (1):**
- `+34 612 345 678 o 0034612345678` → PHONE

**Resultado:** 1 corretos, 1 perdidos, 0 falsos positivos

**Notas:** Formatos de telefone internacionais

---

#### date_roman_numerals [PASS]

**Dificuldade:** hard

**Texto:**
```
Otorgado el día XV de marzo del año MMXXIV.
```

**Esperado (1):**
- `XV de marzo del año MMXXIV` → DATE

**Detectado (1):**
- `día XV de marzo del año MMXXIV` → DATE

**Resultado:** 1 corretos, 0 perdidos, 0 falsos positivos

**Notas:** Data com algarismos romanos (estilo notarial)

---

#### date_ordinal [PASS]

**Dificuldade:** medium

**Texto:**
```
El primero de enero de dos mil veinticuatro.
```

**Esperado (1):**
- `primero de enero de dos mil veinticuatro` → DATE

**Detectado (1):**
- `El primero de enero de dos mil veinticuatro` → DATE

**Resultado:** 1 corretos, 0 perdidos, 0 falsos positivos

**Notas:** Data totalmente escrita por extenso

---

#### address_floor_door [FAIL]

**Dificuldade:** medium

**Texto:**
```
Domicilio en Calle Mayor 15, 3º B, 28001 Madrid.
```

**Esperado (3):**
- `Calle Mayor 15, 3º B` → ADDRESS
- `28001` → POSTAL_CODE
- `Madrid` → LOCATION

**Detectado (1):**
- `Calle Mayor 15, 3º B, 28001 Madrid` → ADDRESS

**Resultado:** 1 corretos, 2 perdidos, 0 falsos positivos

**Notas:** Endereço com andar e porta

---

### ADVERSARIAL

#### negation_dni [PASS]

**Dificuldade:** hard

**Texto:**
```
El interesado manifiesta NO tener DNI ni NIE.
```

**Esperado (0):**
- (nenhuma entidade)

**Detectado (0):**
- (nenhuma entidade)

**Resultado:** 0 corretos, 0 perdidos, 0 falsos positivos

**Notas:** NÃO deve detectar PII - contexto de negação

---

#### example_dni [FAIL]

**Dificuldade:** hard

**Texto:**
```
El formato del DNI es 12345678X (ejemplo ilustrativo).
```

**Esperado (0):**
- (nenhuma entidade)

**Detectado (1):**
- `12345678X` → LICENSE_PLATE

**Resultado:** 0 corretos, 0 perdidos, 1 falsos positivos

**Notas:** Contexto exemplo/ilustrativo deve ser ignorado

---

#### fictional_person [FAIL]

**Dificuldade:** hard

**Texto:**
```
Como dijo Don Quijote de la Mancha en su célebre obra.
```

**Esperado (0):**
- (nenhuma entidade)

**Detectado (1):**
- `Don Quijote de la Mancha` → PERSON

**Resultado:** 0 corretos, 0 perdidos, 1 falsos positivos

**Notas:** Personagem fictício/literário - não PII

---

#### organization_as_person [PASS]

**Dificuldade:** medium

**Texto:**
```
García y Asociados, S.L. interpone demanda.
```

**Esperado (1):**
- `García y Asociados, S.L.` → ORGANIZATION

**Detectado (1):**
- `García y Asociados, S.L.` → ORGANIZATION

**Resultado:** 1 corretos, 0 perdidos, 0 falsos positivos

**Notas:** Sobrenome no nome da empresa - deveria ser ORG não PERSON

---

#### location_as_person [PASS]

**Dificuldade:** hard

**Texto:**
```
El municipio de San Fernando del Valle de Catamarca.
```

**Esperado (1):**
- `San Fernando del Valle de Catamarca` → LOCATION

**Detectado (1):**
- `San Fernando del Valle de Catamarca` → LOCATION

**Resultado:** 1 corretos, 0 perdidos, 0 falsos positivos

**Notas:** Localização com prefixo do tipo pessoa (San)

---

#### date_in_reference [FAIL]

**Dificuldade:** hard

**Texto:**
```
Según la Ley 15/2022, de 12 de julio, reguladora...
```

**Esperado (0):**
- (nenhuma entidade)

**Detectado (3):**
- `Ley 15/` → ECLI
- `2022` → LICENSE_PLATE
- `, de 12 de julio` → ECLI

**Resultado:** 0 corretos, 0 perdidos, 3 falsos positivos

**Notas:** Data em referência legal - não PII independente

---

#### numbers_not_dni [PASS]

**Dificuldade:** medium

**Texto:**
```
El expediente 12345678 consta de 9 folios.
```

**Esperado (0):**
- (nenhuma entidade)

**Detectado (0):**
- (nenhuma entidade)

**Resultado:** 0 corretos, 0 perdidos, 0 falsos positivos

**Notas:** Número de 8 dígitos que NÃO é um DNI (número de processo)

---

#### mixed_languages [FAIL]

**Dificuldade:** hard

**Texto:**
```
Mr. John Smith, con pasaporte UK123456789, residente en Madrid.
```

**Esperado (3):**
- `John Smith` → PERSON
- `UK123456789` → DNI_NIE
- `Madrid` → LOCATION

**Detectado (3):**
- `Mr. John Smith` → PERSON
- `UK123456789` → NSS
- `Madrid` → LOCATION

**Resultado:** 2 corretos, 1 perdidos, 1 falsos positivos

**Notas:** Nome inglês e passaporte estrangeiro

---

### CORRUPÇÃO OCR

#### ocr_letter_substitution [FAIL]

**Dificuldade:** medium

**Texto:**
```
DNl 12345678Z perteneciente a María García.
```

**Esperado (2):**
- `12345678Z` → DNI_NIE
- `María García` → PERSON

**Detectado (4):**
- `DN` → CADASTRAL_REF
- `l 12345678` → NSS
- `Z` → CADASTRAL_REF
- `María García` → PERSON

**Resultado:** 1 corretos, 1 perdidos, 3 falsos positivos

**Notas:** OCR confundiu l com I

---

#### ocr_zero_o_confusion [FAIL]

**Dificuldade:** hard

**Texto:**
```
IBAN ES91 21O0 0418 45O2 OOO5 1332.
```

**Esperado (1):**
- `ES91 21O0 0418 45O2 OOO5 1332` → IBAN

**Detectado (1):**
- `IBAN ES91 21O0 0418 45O2 OOO5 1332` → CADASTRAL_REF

**Resultado:** 0 corretos, 1 perdidos, 1 falsos positivos

**Notas:** OCR confundiu 0 com O

---

#### ocr_missing_spaces [FAIL]

**Dificuldade:** hard

**Texto:**
```
DonJoséGarcíaLópezconDNI12345678X.
```

**Esperado (2):**
- `JoséGarcíaLópez` → PERSON
- `12345678X` → DNI_NIE

**Detectado (2):**
- `DonJoséGarcíaLópezcon` → PERSON
- `DNI12345678X` → CADASTRAL_REF

**Resultado:** 1 corretos, 1 perdidos, 1 falsos positivos

**Notas:** OCR perdeu todos os espaços

---

#### ocr_extra_spaces [FAIL]

**Dificuldade:** hard

**Texto:**
```
D N I  1 2 3 4 5 6 7 8 Z  de  M a r í a.
```

**Esperado (2):**
- `1 2 3 4 5 6 7 8 Z` → DNI_NIE
- `M a r í a` → PERSON

**Detectado (2):**
- `D N I  1 2 3 4 5 6 7 8 Z` → CADASTRAL_REF
- `M` → LOCATION

**Resultado:** 0 corretos, 2 perdidos, 2 falsos positivos

**Notas:** OCR adicionou espaços extras

---

#### ocr_accent_loss [PASS]

**Dificuldade:** easy

**Texto:**
```
Jose Maria Garcia Lopez, vecino de Malaga.
```

**Esperado (2):**
- `Jose Maria Garcia Lopez` → PERSON
- `Malaga` → LOCATION

**Detectado (2):**
- `Jose Maria Garcia Lopez` → PERSON
- `Malaga` → LOCATION

**Resultado:** 2 corretos, 0 perdidos, 0 falsos positivos

**Notas:** OCR perdeu acentos (comum)

---

### EVASÃO UNICODE

#### cyrillic_o [PASS]

**Dificuldade:** hard

**Texto:**
```
DNI 12345678Х pertenece a María.
```

**Esperado (2):**
- `12345678Х` → DNI_NIE
- `María` → PERSON

**Detectado (2):**
- `12345678Х` → DNI_NIE
- `María` → PERSON

**Resultado:** 2 corretos, 0 perdidos, 0 falsos positivos

**Notas:** Cirílico Х (U+0425) em vez de Latino X

---

#### zero_width_space [PASS]

**Dificuldade:** hard

**Texto:**
```
DNI 123​456​78Z de María García.
```

**Esperado (2):**
- `12345678Z` → DNI_NIE
- `María García` → PERSON

**Detectado (2):**
- `123​456​78Z` → DNI_NIE
- `María García` → PERSON

**Resultado:** 2 corretos, 0 perdidos, 0 falsos positivos

**Notas:** Espaços de largura zero inseridos (U+200B)

---

#### fullwidth_numbers [FAIL]

**Dificuldade:** hard

**Texto:**
```
DNI １２３４５６７８Z de María.
```

**Esperado (2):**
- `１２３４５６７８Z` → DNI_NIE
- `María` → PERSON

**Detectado (1):**
- `María` → LOCATION

**Resultado:** 0 corretos, 2 perdidos, 1 falsos positivos

**Notas:** Dígitos de largura total (U+FF11-U+FF19)

---

### MUNDO REAL

#### notarial_header [FAIL]

**Dificuldade:** medium

**Texto:**
```
NÚMERO MIL DOSCIENTOS TREINTA Y CUATRO.- En la ciudad de Sevilla, a quince de marzo de dos mil veinticuatro, ante mí, JOSÉ GARCÍA LÓPEZ, Notario del Ilustre Colegio de Sevilla.
```

**Esperado (4):**
- `Sevilla` → LOCATION
- `quince de marzo de dos mil veinticuatro` → DATE
- `JOSÉ GARCÍA LÓPEZ` → PERSON
- `Sevilla` → LOCATION

**Detectado (4):**
- `NÚMERO MIL DOSCIENTOS TREINTA Y CUATRO.-` → DATE
- `Sevilla` → LOCATION
- `JOSÉ GARCÍA LÓPEZ` → PERSON
- `Ilustre Colegio de Sevilla` → ORGANIZATION

**Resultado:** 2 corretos, 2 perdidos, 2 falsos positivos

**Notas:** Cabeçalho padrão de escritura notarial

---

#### testament_comparecencia [FAIL]

**Dificuldade:** hard

**Texto:**
```
COMPARECE: Doña MARÍA ANTONIA FERNÁNDEZ RUIZ, mayor de edad, viuda, natural de Córdoba, vecina de Madrid, con domicilio en Calle Alcalá número 123, piso 4º, puerta B, y con D.N.I. número 12345678-Z.
```

**Esperado (5):**
- `MARÍA ANTONIA FERNÁNDEZ RUIZ` → PERSON
- `Córdoba` → LOCATION
- `Madrid` → LOCATION
- `Calle Alcalá número 123, piso 4º, puerta B` → ADDRESS
- `12345678-Z` → DNI_NIE

**Detectado (10):**
- `Doña MARÍA ANTONIA FERNÁNDEZ RUIZ` → PERSON
- `Córdoba` → LOCATION
- `Madrid` → LOCATION
- `Calle Alcalá número 123, piso 4º, puerta B,` → ADDRESS
- `D` → PROFESSIONAL_ID
- `.N` → IBAN
- `.` → PROFESSIONAL_ID
- `I` → IBAN
- `.` → PROFESSIONAL_ID
- `12345678-Z` → DNI_NIE

**Resultado:** 5 corretos, 0 perdidos, 5 falsos positivos

**Notas:** Cláusula de comparecimento testamentário

---

#### judicial_sentence_header [FAIL]

**Dificuldade:** hard

**Texto:**
```
SENTENCIA Nº 123/2024. En Madrid, a diez de enero de dos mil veinticuatro. Vistos por la Sala Primera del Tribunal Supremo los recursos interpuestos por D. ANTONIO PÉREZ MARTÍNEZ, representado por el Procurador D. CARLOS SÁNCHEZ GÓMEZ.
```

**Esperado (4):**
- `Madrid` → LOCATION
- `diez de enero de dos mil veinticuatro` → DATE
- `ANTONIO PÉREZ MARTÍNEZ` → PERSON
- `CARLOS SÁNCHEZ GÓMEZ` → PERSON

**Detectado (8):**
- `ENCIA Nº 123` → PROFESSIONAL_ID
- `/2024.` → NSS
- `Madrid` → LOCATION
- `diez de enero de dos mil veinticuatro` → DATE
- `Sala Primera del Tribunal Supremo` → ORGANIZATION
- `D. ANTONIO PÉREZ MARTÍNEZ` → PERSON
- `Procur` → PERSON
- `D. CARLOS SÁNCHEZ GÓMEZ` → PERSON

**Resultado:** 4 corretos, 0 perdidos, 4 falsos positivos

**Notas:** Cabeçalho de sentença do Supremo Tribunal

---

#### contract_parties [FAIL]

**Dificuldade:** hard

**Texto:**
```
De una parte, INMOBILIARIA GARCÍA, S.L., con CIF B-12345678, domiciliada en Plaza Mayor 1, 28013 Madrid, representada por D. PEDRO GARCÍA LÓPEZ. De otra parte, Dña. ANA MARTÍNEZ RUIZ, con NIF 87654321-X.
```

**Esperado (8):**
- `INMOBILIARIA GARCÍA, S.L.` → ORGANIZATION
- `B-12345678` → DNI_NIE
- `Plaza Mayor 1` → ADDRESS
- `28013` → POSTAL_CODE
- `Madrid` → LOCATION
- `PEDRO GARCÍA LÓPEZ` → PERSON
- `ANA MARTÍNEZ RUIZ` → PERSON
- `87654321-X` → DNI_NIE

**Detectado (6):**
- `INMOBILIARIA GARCÍA, S.L.,` → ORGANIZATION
- `B-12345678` → DNI_NIE
- `Plaza Mayor 1, 28013 Madrid` → ADDRESS
- `D. PEDRO GARCÍA LÓPEZ` → PERSON
- `Dña. ANA MARTÍNEZ RUIZ` → PERSON
- `87654321-X` → DNI_NIE

**Resultado:** 6 corretos, 2 perdidos, 0 falsos positivos

**Notas:** Cláusula de partes do contrato

---

#### bank_account_clause [FAIL]

**Dificuldade:** medium

**Texto:**
```
El pago se efectuará mediante transferencia a la cuenta IBAN ES12 0049 1234 5012 3456 7890 titularidad de CONSTRUCCIONES PÉREZ, S.A., con CIF A-98765432.
```

**Esperado (3):**
- `ES12 0049 1234 5012 3456 7890` → IBAN
- `CONSTRUCCIONES PÉREZ, S.A.` → ORGANIZATION
- `A-98765432` → DNI_NIE

**Detectado (9):**
- `IB` → NSS
- `AN` → NSS
- `ES12 0049 1234 5012 3456 7890` → NSS
- `CONSTRUCCIONES PÉREZ, S.A.,` → ORGANIZATION
- `A` → DNI_NIE
- `-` → DNI_NIE
- `98765` → NSS
- `4` → DNI_NIE
- `32` → NSS

**Resultado:** 2 corretos, 1 perdidos, 7 falsos positivos

**Notas:** Cláusula de transferência bancária

---

#### cadastral_reference [FAIL]

**Dificuldade:** medium

**Texto:**
```
Finca registral número 12345 del Registro de la Propiedad de Málaga, con referencia catastral 1234567AB1234S0001AB.
```

**Esperado (2):**
- `Málaga` → LOCATION
- `1234567AB1234S0001AB` → CADASTRAL_REF

**Detectado (5):**
- `número 12345 del Registro de la` → PROFESSIONAL_ID
- `Propiedad` → ORGANIZATION
- `de` → PROFESSIONAL_ID
- `Málaga` → ORGANIZATION
- `1234567AB1234S0001AB` → CADASTRAL_REF

**Resultado:** 1 corretos, 1 perdidos, 4 falsos positivos

**Notas:** Registro de propriedade com referência cadastral

---

#### professional_ids [FAIL]

**Dificuldade:** hard

**Texto:**
```
Interviene el Abogado D. LUIS SÁNCHEZ, colegiado nº 12345 del ICAM, y el Procurador D. MIGUEL TORRES, colegiado nº 67890 del Colegio de Procuradores de Madrid.
```

**Esperado (4):**
- `LUIS SÁNCHEZ` → PERSON
- `12345` → PROFESSIONAL_ID
- `MIGUEL TORRES` → PERSON
- `67890` → PROFESSIONAL_ID

**Detectado (3):**
- `Abogado D. LUIS SÁNCHEZ` → PERSON
- `Procur` → PERSON
- `Colegio de Procuradores de Madrid` → ORGANIZATION

**Resultado:** 1 corretos, 3 perdidos, 2 falsos positivos

**Notas:** Números de ordem profissional

---

#### ecli_citation [PASS]

**Dificuldade:** easy

**Texto:**
```
Según doctrina del Tribunal Supremo (ECLI:ES:TS:2023:1234), confirmada en ECLI:ES:AN:2024:567.
```

**Esperado (2):**
- `ECLI:ES:TS:2023:1234` → ECLI
- `ECLI:ES:AN:2024:567` → ECLI

**Detectado (4):**
- `Tribunal Supremo` → ORGANIZATION
- `(ECLI:ES:TS:2023:1234),` → ECLI
- `E` → ECLI
- `CLI:ES:AN:2024:567` → ECLI

**Resultado:** 2 corretos, 0 perdidos, 2 falsos positivos

**Notas:** Citações de casos ECLI

---

#### vehicle_clause [PASS]

**Dificuldade:** medium

**Texto:**
```
El vehículo marca SEAT, modelo Ibiza, matrícula 1234 ABC, propiedad de D. FRANCISCO LÓPEZ.
```

**Esperado (2):**
- `1234 ABC` → LICENSE_PLATE
- `FRANCISCO LÓPEZ` → PERSON

**Detectado (3):**
- `SEAT` → LICENSE_PLATE
- `modelo Ibiza, matrícula 1234 ABC` → LICENSE_PLATE
- `D. FRANCISCO LÓPEZ` → PERSON

**Resultado:** 2 corretos, 0 perdidos, 1 falsos positivos

**Notas:** Cláusula de descrição do veículo

---

#### social_security [PASS]

**Dificuldade:** easy

**Texto:**
```
Trabajador afiliado a la Seguridad Social con número 281234567890, adscrito al Régimen General.
```

**Esperado (1):**
- `281234567890` → NSS

**Detectado (3):**
- `Seguridad Social` → ORGANIZATION
- `281234567890` → NSS
- `Régimen General` → ORGANIZATION

**Resultado:** 1 corretos, 0 perdidos, 2 falsos positivos

**Notas:** Número de segurança social no contexto de emprego

---


## Metodologia

### Design de Testes

35 casos de teste foram projetados agrupados em 5 categorias de acordo com a taxonomia definida nas diretrizes do projeto:

| Categoria | Testes | Objetivo |
|-----------|-------|----------|
| edge_case | 9 | Condições de limite (nomes curtos, formatos incomuns) |
| adversarial | 8 | Casos projetados para confundir (negações, exemplos, ficção) |
| ocr_corruption | 5 | Simulação de erros de digitalização (l/I, 0/O, espaços) |
| unicode_evasion | 3 | Caracteres semelhantes (Cirílico, largura total, largura zero) |
| real_world | 10 | Padrões reais de documentos legais espanhóis |

### Critérios de Avaliação

- **PASS (easy/medium):** Todas as entidades esperadas detectadas
- **PASS (hard):** Todas as entidades detectadas E zero falsos positivos
- **Matching:** Correspondência fuzzy com tolerância de ±2 caracteres e 80% de similaridade

### Reprodutibilidade

```bash
cd ml
source .venv/bin/activate
python scripts/adversarial/evaluate_adversarial.py
```

---

## Análise de Erros

### Erro 1: Fragmentação de Entidade Composta

**Padrão:** Sequências com pontuação interna fragmentam-se incorretamente.

**Exemplo:**
```
Entrada: "con D.N.I. número 12345678-Z"
Esperado: 12345678-Z → DNI_NIE
Detectado: D → PROFESSIONAL_ID, .N → IBAN, . → PROFESSIONAL_ID, I → IBAN, . → PROFESSIONAL_ID, 12345678-Z → DNI_NIE
```

**Causa:** O modelo não viu padrões com pontuação variável no treinamento sintético.

**Solução proposta:** Pré-processamento regex para normalizar `D.N.I.`, `N.I.F.`, `C.I.F.` → `DNI`, `NIF`, `CIF`.

---

### Erro 2: Confusão de Tipo em Sequências Numéricas

**Padrão:** Sequências numéricas longas classificadas como tipo incorreto.

**Exemplo:**
```
Entrada: "IBAN ES12 0049 1234 5012 3456 7890"
Esperado: ES12 0049 1234 5012 3456 7890 → IBAN
Detectado: ES12 0049 1234 5012 3456 7890 → NSS
```

**Causa:** Sobreposição de padrão numérico entre IBAN (24 caracteres), NSS (12 dígitos), CADASTRAL_REF (20 caracteres).

**Solução proposta:** Pós-processamento com validação de formato específico por tipo.

---

### Erro 3: Falsos Positivos em Referências Legais

**Padrão:** Números em contexto legal (leis, números de processo, protocolos) detectados como PII.

**Exemplo:**
```
Entrada: "Según la Ley 15/2022, de 12 de julio"
Esperado: (nenhuma entidade)
Detectado: Ley 15/ → ECLI, 2022 → LICENSE_PLATE, de 12 de julio → ECLI
```

**Causa:** Padrões `\d+/\d{4}` e datas aparecem em contexto legal, não como PII.

**Solução proposta:** Pós-processamento para excluir padrões `Ley \d+/\d{4}`, `Real Decreto`, `expediente \d+`.

---

### Erro 4: Vulnerabilidade a Erros de OCR

**Padrão:** Confusões típicas de OCR (l/I, 0/O, espaços) quebram a detecção.

**Exemplo:**
```
Entrada: "DNl 12345678Z" (l minúsculo em vez de I)
Esperado: 12345678Z → DNI_NIE
Detectado: DN → CADASTRAL_REF, l 12345678 → NSS, Z → CADASTRAL_REF
```

**Causa:** O modelo treinou apenas com texto limpo, não com variantes OCR.

**Solução proposta:** Pré-processamento com normalização de OCR:
- `DNl` → `DNI`
- `0` ↔ `O` em contexto numérico
- Colapsar espaços em padrões conhecidos

---

### Erro 5: Cegueira Contextual

**Padrão:** O modelo não distingue menções ilustrativas de dados reais.

**Exemplo:**
```
Entrada: "El formato del DNI es 12345678X (ejemplo ilustrativo)"
Esperado: (nenhuma entidade - é um exemplo)
Detectado: 12345678X → LICENSE_PLATE
```

**Causa:** O modelo não tem acesso ao contexto semântico ("exemplo", "formato", "ilustrativo").

**Solução proposta:** Pós-processamento com detecção de contexto:
- Excluir se "ejemplo", "formato", "ilustrativo" aparecer na janela de ±10 tokens
- Requer análise mais sofisticada (parcialmente solucionável com regex)

---

### Erro 6: Entidades Fictícias Detectadas

**Padrão:** Personagens literários/fictícios detectados como pessoas reais.

**Exemplo:**
```
Entrada: "Como dijo Don Quijote de la Mancha"
Esperado: (nenhuma entidade - personagem fictício)
Detectado: Don Quijote de la Mancha → PERSON
```

**Causa:** O modelo não possui lista de personagens fictícios conhecidos.

**Solução proposta:** Pós-processamento com gazetteer de exclusão (personagens fictícios, figuras públicas históricas).

---

## Classificação de Soluções

### Solucionável com Regex (Pré-processo)

| Problema | Regex | Exemplo |
|----------|-------|---------|
| Normalizar D.N.I. | `D\.?\s*N\.?\s*I\.?` → `DNI` | `D.N.I.` → `DNI` |
| Normalizar N.I.F. | `N\.?\s*I\.?\s*F\.?` → `NIF` | `N.I.F.` → `NIF` |
| Colapsar espaços no DNI | `(\d)\s+(\d)` → `\1\2` | `12 345 678` → `12345678` |
| Largura total → ASCII | `[\uFF10-\uFF19]` → `[0-9]` | `１２３` → `123` |
| Remoção de largura zero | `[\u200b\u200c\u200d]` → `` | invisível → removido |
| OCR l/I no DNI | `DN[lI1]` → `DNI` | `DNl` → `DNI` |
| OCR 0/O no IBAN | `[0O]` normalização contextual | `21O0` → `2100` |

### Solucionável com Regex (Pós-processo)

| Problema | Regex/Validação | Ação |
|----------|------------------|--------|
| Ley X/YYYY | `Ley\s+\d+/\d{4}` | Excluir entidade se corresponder |
| Número de processo | `expediente\s+\d+` | Excluir entidade |
| Protocolo NÚMERO | `NÚMERO\s+[A-Z\s]+\.-` | Excluir se detectado como DATE |
| Checksum DNI | Validar letra mod-23 | Rejeitar se inválido |
| Checksum IBAN | Validar dígitos de controle | Rejeitar se inválido |
| Checksum NSS | Validar mod-97 | Rejeitar se inválido |
| Formato de placa | `\d{4}\s?[A-Z]{3}` | Rejeitar se não corresponder |
| Contexto exemplo | `(ejemplo\|ilustrativo\|formato)` próximo | Excluir entidade |

### Requer Modelo/NLP (Não Regex)

| Problema | Solução Necessária |
|----------|-------------------|
| Personagens fictícios | Gazetteer de exclusão + NER específico |
| Truncamento OCR ("Procur") | Melhor tokenização ou modelo robusto |
| Ambiguidade semântica profunda | Fine-tuning com exemplos negativos |

---

## Conclusões

### Pontos Fortes do Modelo

1. **Padrões limpos:** 100% de precisão em testes fáceis com formato padrão
2. **Nomes compostos:** Detecta corretamente nomes nobres longos ("José María de la Santísima Trinidad...")
3. **Negação simples:** Reconhece "NÃO ter DNI" e não detecta falsos positivos
4. **Discriminação ORG/PERSON:** Distingue "García y Asociados, S.L." como organização
5. **Locais com prefixo:** "San Fernando del Valle" corretamente como LOCATION
6. **Robustez parcial Unicode:** Resiste a Cirílico e espaços de largura zero

### Fraquezas Identificadas

1. **Overfitting para dados sintéticos:** 99.87% F1 no teste → 45.7% no adversarial
2. **Fragilidade ao OCR:** 80% de falha na categoria ocr_corruption
3. **Explosão de falsos positivos:** Em textos complexos gera 5-10 detecções espúrias
4. **Confusão de tipo numérico:** IBAN ↔ NSS ↔ CADASTRAL_REF
5. **Cegueira contextual:** Não distingue exemplos, referências legais, ficção

### Métricas Chave

| Métrica | Valor | Alvo | Status |
|---------|-------|----------|--------|
| F1 sintético | 99.87% | ≥85% | ✅ Aprovado |
| F1 adversarial (estimado) | ~45% | ≥70% | ❌ Não Alcançado |
| Taxa de falsos positivos | Alta | Baixa | ❌ Crítico |
| Robustez OCR | 20% | ≥80% | ❌ Crítico |

---

## Trabalho Futuro

### Prioridade ALTA (Implementar Imediatamente)

1. **Pipeline de Pré/Pós-processamento**
   - Criar `scripts/inference/text_normalizer.py` (pré-processo)
   - Criar `scripts/inference/entity_validator.py` (pós-processo)
   - Integrar no pipeline de inferência

2. **Validação de Checksum**
   - DNI: letra = "TRWAGMYFPDXBNJZSQVHLCKE"[número % 23]
   - IBAN: dígitos de controle válidos
   - NSS: validação mod-97

3. **Gazetteers de Exclusão**
   - Personagens fictícios conhecidos
   - Padrões legais (Ley, RD, número de processo)

### Prioridade MÉDIA (Próxima Iteração)

4. **Aumento de Dados**
   - Adicionar exemplos com erros de OCR ao conjunto de dados
   - Adicionar exemplos negativos (números que NÃO são PII)
   - Adicionar contextos de "exemplo ilustrativo"

5. **Re-treinamento**
   - Com conjunto de dados aumentado
   - Avaliar camada CRF (+4-13% F1 de acordo com a literatura)

### Prioridade BAIXA (Futuro)

6. **Dados Reais Anotados**
   - Obter documentos legais reais anonimizados
   - Anotação manual de padrão ouro

---

## Referências

1. **Modelo base:** PlanTL-GOB-ES/roberta-base-bne-capitel-ner
2. **Metodologia adversarial:** diretrizes do projeto, seção 4 (Teste Adversarial)
3. **Validação DNI:** BOE - Algoritmo de letra NIF
4. **Validação IBAN:** ISO 13616 - International Bank Account Number
5. **seqeval:** Framework de avaliação NER (nível de entidade)

---

**Gerado por:** `scripts/adversarial/evaluate_adversarial.py`
**Data:** 2026-01-20
**Versão:** 1.0
