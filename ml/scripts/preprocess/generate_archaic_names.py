#!/usr/bin/env python3
"""
Generate synthetic archaic Spanish names for NER training.

Combines:
- Exhaustive list of archaic first names (500+ per gender)
- All rare surnames from INE data
- Legal document naming patterns (Don/Doña, compound names)

Output: gazetteers/nombres_arcaicos.json
"""

import json
import random
from pathlib import Path


BASE_DIR = Path(__file__).parent.parent.parent
GAZETTEERS_DIR = BASE_DIR / "gazetteers"

# =============================================================================
# EXHAUSTIVE ARCHAIC FIRST NAMES - HOMBRES (500+)
# =============================================================================

NOMBRES_ARCAICOS_HOMBRES = [
    # =========================================================================
    # SANTOS Y MÁRTIRES (muy comunes en España pre-1950)
    # =========================================================================
    "OBDULIO", "EPIFANIO", "PRIMITIVO", "VICTORIANO", "EUSEBIO",
    "BONIFACIO", "CRISANTO", "EULOGIO", "HERMÓGENES", "NICOMEDES",
    "POLICARPO", "SATURNINO", "TEÓFILO", "VENANCIO", "ZENÓN",
    "ANACLETO", "BAUDILIO", "CLEMENTE", "DEMETRIO", "EMETERIO",
    "FACUNDO", "GENARO", "HELIODORO", "INDALECIO", "JUSTO",
    "LADISLAO", "MACARIO", "NARCISO", "OLEGARIO", "PANCRACIO",
    "QUIRINO", "RECAREDO", "SERVANDO", "TIBURCIO", "URBANO",
    "ABUNDIO", "ACACIO", "AGAPITO", "ALBINO", "AMANCIO",
    "AMBROSIO", "ANASTASIO", "ANIANO", "ANICETO", "ANSELMO",
    "ANTOLÍN", "APOLINAR", "AQUILINO", "ARCADIO", "ARSENIO",
    "ATANASIO", "AURELIANO", "BASILIO", "BAUTISTA", "BENIGNO",
    "BERNARDINO", "BLAS", "BRAULIO", "BUENAVENTURA", "CALIXTO",
    "CAMERINO", "CÁNDIDO", "CASIANO", "CASIMIRO", "CAYETANO",
    "CELEDONIO", "CELESTINO", "CIPRIANO", "CIRILO", "CLAUDIO",
    "CORNELIO", "COSME", "CRISÓSTOMO", "CRISTÓBAL", "DAMIÁN",
    "DESIDERIO", "DIONISIO", "DOMINGO", "DONATO", "EDELMIRO",
    "EDMUNDO", "ELEUTERIO", "ELÍAS", "ELISEO", "EMILIANO",
    "EPIFANIO", "ERASMO", "EUTIQUIO", "EVARISTO", "EZEQUIEL",
    "FABIÁN", "FAUSTINO", "FAUSTO", "FELICIANO", "FÉLIX",
    "FERMÍN", "FIDEL", "FILOMENO", "FLORENCIO", "FLORENTINO",
    "FORTUNATO", "FRUCTUOSO", "FULGENCIO", "GABINO", "GAUDENCIO",
    "GELASIO", "GERARDO", "GERMÁN", "GERVASIO", "GIL",
    "GINÉS", "GODOFREDO", "GONZALO", "GREGORIO", "GUIDO",
    "GUILLERMO", "HERACLIO", "HERMENEGILDO", "HIGINIO", "HILARIO",
    "HIPÓLITO", "HONORIO", "HORACIO", "HUGO", "HUMBERTO",
    "IGNACIO", "INOCENCIO", "IRENEO", "ISIDORO", "ISIDRO",
    "JACINTO", "JACOBO", "JENARO", "JERÓNIMO", "JOAQUÍN",
    "JONÁS", "JORDÁN", "JOSUÉ", "JULIÁN", "JUSTINIANO",
    "JUSTINO", "JUVENAL", "LAMBERTO", "LAUREANO", "LÁZARO",
    "LEANDRO", "LEOVIGILDO", "LEOPOLDINO", "LEOPOLDO", "LIBERATO",
    "LIBORIO", "LICINIO", "LISARDO", "LOPE", "LORENZO",
    "LUCAS", "LUCIANO", "LUCIO", "LUPO", "MACROBIO",
    "MAMERTO", "MARCELINO", "MARCELO", "MARCIANO", "MARCOS",
    "MARIANO", "MARTINIANO", "MATEO", "MATÍAS", "MAURICIO",
    "MÁXIMO", "MELCHOR", "METODIO", "MILLÁN", "MODESTO",
    "MOISÉS", "NATALIO", "NAZARIO", "NEMESIO", "NEREO",
    "NÉSTOR", "NICANDRO", "NICANOR", "NICASIO", "NICÉFORO",
    "NICOLÁS", "NORBERTO", "OCTAVIO", "ODÓN", "ONÉSIMO",
    "ÓSCAR", "OSWALDO", "OTILIO", "OVIDIO", "PACIANO",
    "PACOMIO", "PANTALEÓN", "PASCUAL", "PASTOR", "PATRICIO",
    "PAULINO", "PEDRO", "PELAYO", "PERFECTO", "PETRONILO",
    "PÍO", "PLÁCIDO", "PLINIO", "PLUTARCO", "POLICARPO",
    "POMPEYO", "PONCIANO", "PORFIRIO", "PRÁXEDES", "PRIMO",
    "PRISCILIANO", "PROCOPIO", "PRÓSPERO", "PRUDENCIO", "QUERUBÍN",
    "QUINTÍN", "QUIRICO", "RAIMUNDO", "RAMIRO", "REGINALDO",
    "REMIGIO", "RENATO", "RIGOBERTO", "ROBUSTIANO", "RODOLFO",
    "RODRIGO", "ROGELIO", "ROMÁN", "ROMUALDO", "ROQUE",
    "ROSENDO", "RUFINO", "RUPERTO", "SABAS", "SABINO",
    "SALUSTIANO", "SALVADOR", "SANCHO", "SANDRO", "SANTIAGO",
    "SATURNINO", "SEBASTIÁN", "SECUNDINO", "SEGISMUNDO", "SENÉN",
    "SERGIO", "SEVERIANO", "SEVERINO", "SEVERO", "SILVANO",
    "SILVERIO", "SILVESTRE", "SILVINO", "SIMEÓN", "SIMÓN",
    "SINFORIANO", "SIXTO", "SOFRONIO", "SOTERO", "TARSICIO",
    "TELESFORO", "TEODOMIRO", "TEODORO", "TEODOSIO", "TEÓFANES",
    "TERCIO", "TIMOTEO", "TITO", "TOMÁS", "TORIBIO",
    "TRANQUILINO", "TRISTÁN", "UBALDO", "ULPIANO", "URBICIO",
    "URSICINO", "VALERIANO", "VALERIO", "VENTURA", "VEREMUNDO",
    "VÍCTOR", "VICTORINO", "VIRGILIO", "WENCESLAO", "WILFRIDO",
    "ZACARÍAS", "ZENOBIO",

    # =========================================================================
    # VISIGODOS Y MEDIEVALES ESPAÑOLES
    # =========================================================================
    "ATAÚLFO", "ALARICO", "ALDOLFO", "ALFONSO", "ALMANZOR",
    "ALVAR", "ÁLVARO", "AMALARICO", "ARDERICO", "ARGIMIRO",
    "ARNALDO", "ATANAGILDO", "AUDAZ", "AURELIO", "BALDOMERO",
    "BERMUDO", "BERNARDO", "CHILDERICO", "CHINDASVINTO", "EGICA",
    "ERVIGIO", "EURICO", "FAVILA", "FERNANDO", "FRUELA",
    "GARCÍA", "GARCILASO", "GELMÍREZ", "GESALEICO", "GIMENO",
    "GODOS", "GUDILA", "GUNDERICO", "GUNDEMARO", "HERMERICO",
    "ÍÑIGO", "JIMENO", "LEOVIGILDO", "LIUVA", "MUNIO",
    "NUÑO", "ORDOÑO", "OSORIO", "PELAYO", "RAMIRO",
    "RECESVINTO", "RECAREDO", "RODRIGO", "SANCHO", "SIGERICO",
    "SISEBUTO", "SISENANDO", "SUINTILA", "TEODORICO", "TEODOMIRO",
    "TEUDIS", "TOTILA", "TURISMUNDO", "VAMBA", "VERMUDO",
    "VITIZA", "WALIA", "WITERICO", "WITIZA",

    # =========================================================================
    # COMPUESTOS TRADICIONALES ESPAÑOLES
    # =========================================================================
    "JOSÉ MARÍA", "JUAN BAUTISTA", "FRANCISCO DE ASÍS", "FRANCISCO DE PAULA",
    "JUAN DE DIOS", "JUAN DE LA CRUZ", "PEDRO PABLO", "JUAN ANTONIO",
    "JOSÉ ANTONIO", "JOSÉ LUIS", "JOSÉ RAMÓN", "JOSÉ MANUEL",
    "JUAN JOSÉ", "JUAN CARLOS", "JUAN MANUEL", "JUAN FRANCISCO",
    "LUIS MARÍA", "MIGUEL ÁNGEL", "CARLOS MARÍA", "ÁNGEL MARÍA",
    "FRANCISCO JAVIER", "ANTONIO MARÍA", "JOSÉ IGNACIO", "JOSÉ MIGUEL",
    "PEDRO ANTONIO", "PEDRO JOSÉ", "PEDRO JUAN", "PEDRO MIGUEL",
    "VICENTE FERRER", "DIEGO DE ALCALÁ", "ISIDRO LABRADOR",
    "ANTONIO DE PADUA", "JUAN EVANGELISTA", "JUAN CRISÓSTOMO",
    "PABLO DE LA CRUZ", "CAYETANO DE THIENE", "FRANCISCO SOLANO",
    "FRANCISCO DE BORJA", "IGNACIO DE LOYOLA", "JUAN DE MATA",
    "FELIPE NERI", "CARLOS BORROMEO", "LUIS GONZAGA", "ESTANISLAO DE KOSTKA",

    # =========================================================================
    # NOMBRES BÍBLICOS Y HEBREOS
    # =========================================================================
    "ABRAHAM", "ADÁN", "AMÓS", "BARUC", "BENJAMÍN",
    "DANIEL", "DAVID", "EFRAÍN", "ELÍAS", "ELISEO",
    "ENOC", "ESDRAS", "EZEQUIEL", "HABACUC", "ISAAC",
    "ISAÍAS", "ISMAEL", "ISRAEL", "JACOB", "JEREMÍAS",
    "JOB", "JOEL", "JONÁS", "JOSUÉ", "MALAQUÍAS",
    "MIQUEAS", "MOISÉS", "NAHÚM", "NATANAEL", "NEHEMÍAS",
    "NOÉ", "OSEAS", "RUBÉN", "SALOMÓN", "SAMUEL",
    "SAÚL", "SIMEÓN", "TOBÍAS", "ZACARÍAS", "ZOROBABEL",

    # =========================================================================
    # GRIEGOS Y LATINOS CULTOS
    # =========================================================================
    "ADRIANO", "AGUSTÍN", "ALEJANDRO", "ALEXIS", "ANAXÁGORAS",
    "ANDRÉS", "ANÍBAL", "ARISTÓTELES", "ARQUÍMEDES", "AUGUSTO",
    "AURELIO", "CÉSAR", "CICERÓN", "CLAUDIO", "CONSTANTINO",
    "DEMÓCRITO", "DIÓGENES", "EMPÉDOCLES", "EPICURO", "ESPARTACO",
    "ESTOICO", "EUCLIDÉS", "FILIPO", "HERÁCLITO", "HIPÓCRATES",
    "HOMERO", "JULIO", "JUVENCIO", "LUCRECIO", "MARCO",
    "NERÓN", "OCTAVIO", "OVIDIO", "PARMÉNIDES", "PITÁGORAS",
    "PLATÓN", "PLINIO", "PLUTARCO", "POMPEYO", "SÉNECA",
    "SÓCRATES", "TALES", "TIBERIO", "TRAJANO", "VIRGILIO",
]

# =============================================================================
# EXHAUSTIVE ARCHAIC FIRST NAMES - MUJERES (500+)
# =============================================================================

NOMBRES_ARCAICOS_MUJERES = [
    # =========================================================================
    # SANTOS Y VÍRGENES (muy comunes en España pre-1950)
    # =========================================================================
    "SERAFINA", "FELICÍSIMA", "ESCOLÁSTICA", "ENCARNACIÓN", "HERMINIA",
    "PURIFICACIÓN", "ASCENSIÓN", "PRESENTACIÓN", "VISITACIÓN", "CONSOLACIÓN",
    "ANGUSTIAS", "REMEDIOS", "ROCÍO", "SOLEDAD", "DOLORES",
    "ASUNCIÓN", "CONCEPCIÓN", "NATIVIDAD", "CANDELARIA", "TRINIDAD",
    "PATROCINIO", "ROSARIO", "MILAGROS", "NIEVES", "SAGRARIO",
    "EDUVIGIS", "GENOVEVA", "HERMELINDA", "ILUMINADA", "JUSTINA",
    "LEOCADIA", "MELITONA", "NEMESIA", "OBDULIA", "PERPETUA",
    "QUITERIA", "RUFINA", "SINFOROSA", "TELESFORA", "ÚRSULA",
    "VENANCIA", "WENCESLADA", "ZENOBIA", "ADELAIDA", "BALBINA",
    "CASILDA", "DOMITILA", "EUSEBIA", "FERMINA", "GERÓNIMA",
    "ABUNDIA", "ACACIA", "AGAPITA", "ÁGUEDA", "ALBINA",
    "ALDEGUNDA", "ALFONSA", "AMALIA", "AMBROSIA", "ANASTASIA",
    "ANICETA", "ANTONIA", "APOLONIA", "AQUILINA", "ARCADIA",
    "ARSENIA", "ATANASIA", "AUREA", "AURELIA", "AVELINA",
    "BASILISA", "BEATRIZ", "BENIGNA", "BERNARDA", "BERNARDINA",
    "BIBIANA", "BIENVENIDA", "BLANCA", "BRAULIA", "BRÍGIDA",
    "CALIOPA", "CÁNDIDA", "CARIDAD", "CARLOTA", "CASIANA",
    "CATALINA", "CELEDONIA", "CELESTE", "CELESTINA", "CIPRIANA",
    "CLARA", "CLAUDIA", "CLEMENTINA", "CLOTILDE", "COLUMBA",
    "CONRADA", "CONSTANCIA", "CORINA", "CORNELIA", "CRESCENCIA",
    "CRISTETA", "CRISTIANA", "DÁMASA", "DANIELA", "DELFINA",
    "DESIDERIA", "DIGNA", "DIONISIA", "DOMINGA", "DOROTEA",
    "EDITA", "EDMUNDA", "EDUVIGES", "ELIA", "ELICIA",
    "ELOÍSA", "ELVIRA", "EMELIA", "EMERENCIANA", "EMILIA",
    "EMILIANA", "ENGRACIA", "EPIFANIA", "ERNESTINA", "ESCOLÁSTICA",
    "ESPERANZA", "ESTEFANÍA", "ETELVINA", "EUFEMIA", "EUFRASIA",
    "EUGENIA", "EULALIA", "EULOGIA", "EUSEBIA", "EUTIMIA",
    "EUTROFIA", "EUTROPIA", "EVA", "EVELINA", "EXALTACIÓN",
    "FABIANA", "FABIOLA", "FAUSTA", "FAUSTINA", "FE",
    "FELICIA", "FELICIANA", "FELIPA", "FILOMENA", "FINA",
    "FLAMINIA", "FLAVIA", "FLOR", "FLORA", "FLORENCIA",
    "FLORENTINA", "FLORIDA", "FLORINDA", "FORTUNATA", "FRANCISCA",
    "FRUCTUOSA", "GALA", "GASPARA", "GEMA", "GENEROSA",
    "GENOVEVA", "GERTRUDIS", "GILA", "GINESA", "GLICERIA",
    "GLORIA", "GORGONIA", "GRACIA", "GRACIANA", "GREGORIA",
    "GRISELDA", "GUADALUPE", "GUIOMAR", "HELIODORA", "HELOÍSA",
    "HERMELINDA", "HERMENEGILDA", "HERMINIA", "HIGINIA", "HILARIA",
    "HONORATA", "HONORINA", "HORTENSIA", "IDOIA", "IFIGENIA",
    "ILDEFONSA", "ILDA", "ILUMINADA", "IMELDA", "INÉS",
    "INOCENCIA", "IRENE", "IRIS", "ISABEL", "ISIDORA",
    "JACINTA", "JAVIERA", "JERÓNIMA", "JESUSA", "JIMENA",
    "JOAQUINA", "JORJA", "JOSEFA", "JOSEFINA", "JOVITA",
    "JUANA", "JULIA", "JULIANA", "JULITA", "JUSTA",
    "JUSTINA", "LAUDELINA", "LAURA", "LAUREANA", "LAURENCIA",
    "LAURENTINA", "LEA", "LEANDRA", "LEOCRICIA", "LEOCADIA",
    "LEONARDA", "LEONIA", "LEONILDA", "LEONOR", "LEOPOLDA",
    "LIBERIA", "LIBRADA", "LIDIA", "LIDUVINA", "LORENZA",
    "LUCÍA", "LUCIANA", "LUCILA", "LUCRECIA", "LUDIVINA",
    "LUISA", "LUPE", "LUZ", "MACARIA", "MADRONA",
    "MAGDALENA", "MARAVILLAS", "MARCELA", "MARCELIANA", "MARCELINA",
    "MARCIA", "MARCIANA", "MARGARITA", "MARINA", "MARTA",
    "MARTINA", "MATILDE", "MÁXIMA", "MAXIMIANA", "MAXIMINA",
    "MELANIA", "MELCHORA", "MELITONA", "MERCEDES", "MICAELA",
    "MIGUELA", "MODESTA", "MÓNICA", "NARCISA", "NATALIA",
    "NATIVIDAD", "NAZARIA", "NEMESIA", "NICASIA", "NICOLASA",
    "NIEVES", "NILDA", "NINFA", "NOEMÍ", "NORBERTA",
    "OBDULIA", "OCTAVIA", "ODILIA", "OLALLA", "OLIMPIA",
    "OLIVA", "OROSIA", "OTILIA", "PALMIRA", "PANCRACIA",
    "PASCUALA", "PASTORA", "PATRICIA", "PATROCINIA", "PAULA",
    "PAULINA", "PAZ", "PEREGRINA", "PERFECTA", "PERPETUA",
    "PETRA", "PETRONILA", "PÍA", "PIEDAD", "PILAR",
    "PLÁCIDA", "POLICARPA", "POMPOSA", "PRÁXEDES", "PRECIOSA",
    "PRESENTACIÓN", "PRIMA", "PRIMITIVA", "PRISCA", "PRISCILA",
    "PRUDENCIA", "PURA", "PURIFICACIÓN", "RAFAELA", "RAMONA",
    "RAQUEL", "REBECA", "REGINA", "REINALDA", "REMEDIOS",
    "RENATA", "RESTITUTA", "RICARDA", "RITA", "ROBERTA",
    "ROBUSTIANA", "ROGELIA", "ROMANA", "ROSA", "ROSALÍA",
    "ROSALINDA", "ROSAURA", "ROSENDA", "RUFINA", "RUPERTA",
    "RÚSTICA", "RUT", "SABINA", "SALOMÉ", "SALUSTIANA",
    "SALVADORA", "SANCHA", "SANTINA", "SARA", "SATURIA",
    "SATURNINA", "SEBASTIANA", "SECUNDINA", "SEGISMUNDA", "SEMPRONIANA",
    "SERENA", "SERVANDA", "SEVERA", "SEVERIANA", "SEVERINA",
    "SILVANA", "SILVERIA", "SILVESTRA", "SILVINA", "SIMPLICIA",
    "SINFORIANA", "SIXTA", "SOFÍA", "SOLEDAD", "SONSOLES",
    "SUSANA", "TADEA", "TARSILA", "TECLA", "TELMA",
    "TEODORA", "TEODOSIA", "TEÓFILA", "TERESA", "TIMOTEA",
    "TOMASA", "TRANQUILINA", "TRIFINA", "TRIFONIA", "TRINIDAD",
    "ÚRSULA", "URSULINA", "VALENTINA", "VALERIA", "VALERIANA",
    "VENERANDA", "VENTURA", "VERÓNICA", "VICENTA", "VICTORIA",
    "VICTORIANA", "VICTORINA", "VILMA", "VIOLETA", "VIRGILIA",
    "VIRGINIA", "VISITACIÓN", "VIVIANA", "WENCESLADA", "WULFRANA",
    "XIMENA", "YOLANDA", "ZENAIDA", "ZENOBIA", "ZOILA",

    # =========================================================================
    # ADVOCACIONES MARIANAS (muy común en España)
    # =========================================================================
    "ALMUDENA", "AMPARO", "ARACELI", "ARANZAZU", "BEGOÑA",
    "BELÉN", "CARMEN", "CARIDAD", "CINTA", "CONSUELO",
    "COVADONGA", "DESAMPARADOS", "ESPERANZA", "ESTRELLA", "FÁTIMA",
    "FUENSANTA", "GRACIA", "GUADALUPE", "INMACULADA", "LORETO",
    "LOURDES", "LUZ", "MACARENA", "MARAVILLAS", "MERCEDES",
    "MISERICORDIA", "MONTAÑA", "MONTSERRAT", "NURIA", "PALOMA",
    "PAZ", "PEÑA", "PIEDAD", "PILAR", "REGLA",
    "REYES", "ROCÍO", "ROSARIO", "SAGRARIO", "SALUD",
    "SOCORRO", "SOLEDAD", "VICTORIA", "VIRTUDES",

    # =========================================================================
    # COMPUESTOS TRADICIONALES ESPAÑOLES
    # =========================================================================
    "MARÍA JOSEFA", "MARÍA DOLORES", "MARÍA ENCARNACIÓN", "MARÍA PURIFICACIÓN",
    "MARÍA ANGUSTIAS", "MARÍA REMEDIOS", "MARÍA SOLEDAD", "ANA MARÍA",
    "MARÍA DEL CARMEN", "MARÍA DE LOS ÁNGELES", "MARÍA DEL PILAR",
    "MARÍA DE LA CONCEPCIÓN", "MARÍA DE LOS DOLORES", "MARÍA LUISA",
    "MARÍA TERESA", "MARÍA ISABEL", "MARÍA ANTONIA", "MARÍA ROSA",
    "MARÍA JESÚS", "MARÍA CRUZ", "MARÍA PAZ", "MARÍA LUZ",
    "MARÍA VICTORIA", "MARÍA MERCEDES", "MARÍA ELENA", "MARÍA EUGENIA",
    "MARÍA CRISTINA", "MARÍA GLORIA", "MARÍA ASUNCIÓN", "MARÍA FE",
    "MARÍA ESPERANZA", "MARÍA NIEVES", "MARÍA ROCÍO", "MARÍA AMPARO",
    "ANA JOSEFA", "ANA ISABEL", "ANA ROSA", "JUANA MARÍA",
    "ROSA MARÍA", "PAULA MARÍA", "CLARA MARÍA", "LUISA MARÍA",
    "JOSEFA MARÍA", "TERESA DE JESÚS", "JUANA DE ARCO", "ROSA DE LIMA",
    "CATALINA DE SIENA", "BRÍGIDA DE SUECIA", "CLARA DE ASÍS",
    "GERTRUDIS LA MAGNA", "HILDEGARDA DE BINGEN", "ISABEL DE HUNGRÍA",
    "MARGARITA MARÍA", "MARÍA GORETTI", "MARÍA AUXILIADORA",

    # =========================================================================
    # NOMBRES BÍBLICOS Y HEBREOS
    # =========================================================================
    "ADA", "ABIGAÍL", "BETSABÉ", "DALILA", "DÉBORA",
    "DINA", "ESTER", "EVA", "JUDIT", "LEA",
    "MARÍA", "MIRIAM", "NOEMÍ", "RAQUEL", "REBECA",
    "RUT", "SALOMÉ", "SARA", "SUSANA", "TAMAR",
]

# =============================================================================
# APELLIDOS COMPUESTOS Y PATRONES
# =============================================================================

APELLIDOS_COMPUESTOS_PATTERNS = [
    "{ap1} DE {ap2}",
    "{ap1}-{ap2}",
    "{ap1} Y {ap2}",
    "DE {ap1}",
    "DEL {ap1}",
    "DE LA {ap1}",
    "DE LOS {ap1}",
    "DE LAS {ap1}",
]

# =============================================================================
# PATRONES DE DOCUMENTOS LEGALES
# =============================================================================

LEGAL_PATTERNS_MALE = [
    "Don {nombre} {ap1} {ap2}",
    "D. {nombre} {ap1} {ap2}",
    "{nombre} {ap1} {ap2}, mayor de edad",
    "{nombre} {ap1} {ap2}, vecino de {municipio}",
    "{nombre} {ap1} {ap2}, natural de {municipio}",
    "{nombre} {ap1} {ap2}, con domicilio en {municipio}",
    "el compareciente Don {nombre} {ap1} {ap2}",
    "el testador Don {nombre} {ap1} {ap2}",
    "el causante Don {nombre} {ap1} {ap2}",
    "el otorgante Don {nombre} {ap1} {ap2}",
    "el poderdante Don {nombre} {ap1} {ap2}",
    "el demandante Don {nombre} {ap1} {ap2}",
    "el demandado Don {nombre} {ap1} {ap2}",
    "el recurrente Don {nombre} {ap1} {ap2}",
    "el apelante Don {nombre} {ap1} {ap2}",
    "el heredero Don {nombre} {ap1} {ap2}",
    "el legatario Don {nombre} {ap1} {ap2}",
    "el fiador Don {nombre} {ap1} {ap2}",
    "el arrendador Don {nombre} {ap1} {ap2}",
    "el arrendatario Don {nombre} {ap1} {ap2}",
    "el vendedor Don {nombre} {ap1} {ap2}",
    "el comprador Don {nombre} {ap1} {ap2}",
    "el acreedor Don {nombre} {ap1} {ap2}",
    "el deudor Don {nombre} {ap1} {ap2}",
]

LEGAL_PATTERNS_FEMALE = [
    "Doña {nombre} {ap1} {ap2}",
    "Dª. {nombre} {ap1} {ap2}",
    "Dña. {nombre} {ap1} {ap2}",
    "{nombre} {ap1} {ap2}, mayor de edad",
    "{nombre} {ap1} {ap2}, vecina de {municipio}",
    "{nombre} {ap1} {ap2}, natural de {municipio}",
    "{nombre} {ap1} {ap2}, con domicilio en {municipio}",
    "la compareciente Doña {nombre} {ap1} {ap2}",
    "la testadora Doña {nombre} {ap1} {ap2}",
    "la causante Doña {nombre} {ap1} {ap2}",
    "la otorgante Doña {nombre} {ap1} {ap2}",
    "la poderdante Doña {nombre} {ap1} {ap2}",
    "la demandante Doña {nombre} {ap1} {ap2}",
    "la demandada Doña {nombre} {ap1} {ap2}",
    "la recurrente Doña {nombre} {ap1} {ap2}",
    "la apelante Doña {nombre} {ap1} {ap2}",
    "la heredera Doña {nombre} {ap1} {ap2}",
    "la legataria Doña {nombre} {ap1} {ap2}",
    "la fiadora Doña {nombre} {ap1} {ap2}",
    "la arrendadora Doña {nombre} {ap1} {ap2}",
    "la arrendataria Doña {nombre} {ap1} {ap2}",
    "la vendedora Doña {nombre} {ap1} {ap2}",
    "la compradora Doña {nombre} {ap1} {ap2}",
    "la acreedora Doña {nombre} {ap1} {ap2}",
    "la deudora Doña {nombre} {ap1} {ap2}",
    "viuda de Don {ap_viudo}",
]


def load_apellidos() -> list[dict]:
    """Load surnames from gazetteers."""
    with open(GAZETTEERS_DIR / "apellidos.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["apellidos"]


def load_municipios() -> list[str]:
    """Load municipalities from gazetteers."""
    with open(GAZETTEERS_DIR / "municipios.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["municipios"]


def get_rare_surnames(apellidos: list[dict], max_freq: int = 10000) -> list[str]:
    """Get surnames with frequency below threshold (rare ones)."""
    return [a["apellido"] for a in apellidos if a["frecuencia"] <= max_freq]


def get_common_surnames(apellidos: list[dict], min_freq: int = 100000) -> list[str]:
    """Get common surnames for realistic combinations."""
    return [a["apellido"] for a in apellidos if a["frecuencia"] >= min_freq]


def generate_compound_surname(ap1: str, ap2: str) -> str:
    """Generate a compound surname using patterns."""
    pattern = random.choice(APELLIDOS_COMPUESTOS_PATTERNS)
    return pattern.format(ap1=ap1, ap2=ap2)


def generate_full_name(
    nombre: str,
    apellidos: list[str],
    municipios: list[str],
    gender: str
) -> dict:
    """Generate a full name with legal context."""
    ap1 = random.choice(apellidos)
    ap2 = random.choice(apellidos)
    municipio = random.choice(municipios)

    # Sometimes use compound surname (20% chance)
    if random.random() < 0.20:
        ap1 = generate_compound_surname(ap1, random.choice(apellidos))

    # Select appropriate pattern based on gender
    if gender == "M":
        pattern = random.choice(LEGAL_PATTERNS_MALE)
        full_text = pattern.format(
            nombre=nombre.title(),
            ap1=ap1.title(),
            ap2=ap2.title(),
            municipio=municipio
        )
    else:
        pattern = random.choice(LEGAL_PATTERNS_FEMALE)
        if "{ap_viudo}" in pattern:
            ap_viudo = random.choice(apellidos)
            full_text = pattern.format(ap_viudo=ap_viudo.title())
        else:
            full_text = pattern.format(
                nombre=nombre.title(),
                ap1=ap1.title(),
                ap2=ap2.title(),
                municipio=municipio
            )

    return {
        "texto": full_text,
        "nombre": nombre,
        "apellido1": ap1,
        "apellido2": ap2,
        "genero": gender,
        "patron": pattern
    }


def main():
    """Generate archaic names dataset."""
    print("=" * 60)
    print("GENERADOR DE NOMBRES ARCAICOS (EXHAUSTIVO)")
    print("=" * 60)

    # Load data
    print("\n[1/4] Loading gazetteers...")
    apellidos = load_apellidos()
    municipios = load_municipios()

    rare_surnames = get_rare_surnames(apellidos, max_freq=5000)
    all_surnames = [a["apellido"] for a in apellidos]

    print(f"    Total surnames: {len(apellidos)}")
    print(f"    Rare surnames (freq < 5000): {len(rare_surnames)}")
    print(f"    Municipalities: {len(municipios)}")
    print(f"    Archaic male names: {len(NOMBRES_ARCAICOS_HOMBRES)}")
    print(f"    Archaic female names: {len(NOMBRES_ARCAICOS_MUJERES)}")

    # Generate names
    print("\n[2/4] Generating archaic name combinations...")

    generated_names = []

    # Generate 5 variants per archaic name
    for nombre in NOMBRES_ARCAICOS_HOMBRES:
        for _ in range(5):
            # Mix of rare and common surnames for realism
            surname_pool = rare_surnames if random.random() < 0.3 else all_surnames
            generated_names.append(generate_full_name(nombre, surname_pool, municipios, "M"))

    for nombre in NOMBRES_ARCAICOS_MUJERES:
        for _ in range(5):
            surname_pool = rare_surnames if random.random() < 0.3 else all_surnames
            generated_names.append(generate_full_name(nombre, surname_pool, municipios, "F"))

    print(f"    Generated {len(generated_names)} name combinations")

    # Create output structure
    print("\n[3/4] Building output...")

    # Deduplicate names
    unique_hombres = sorted(set(NOMBRES_ARCAICOS_HOMBRES))
    unique_mujeres = sorted(set(NOMBRES_ARCAICOS_MUJERES))

    output = {
        "source": "Synthetic - Exhaustive Archaic Spanish Names",
        "description": "Nombres arcaicos españoles exhaustivos para documentos legales",
        "stats": {
            "nombres_arcaicos_hombres": len(unique_hombres),
            "nombres_arcaicos_mujeres": len(unique_mujeres),
            "total_nombres_unicos": len(unique_hombres) + len(unique_mujeres),
            "combinaciones_generadas": len(generated_names),
            "apellidos_disponibles": len(all_surnames),
            "apellidos_raros": len(rare_surnames),
            "municipios": len(municipios),
        },
        "nombres_arcaicos": {
            "hombres": unique_hombres,
            "mujeres": unique_mujeres
        },
        "apellidos_raros_sample": rare_surnames[:200],
        "ejemplos_generados": random.sample(generated_names, min(500, len(generated_names))),
    }

    # Flat list for direct NER training
    flat_names = {
        "todos_nombres": sorted(set(unique_hombres + unique_mujeres)),
        "ejemplos_contexto": [g["texto"] for g in generated_names]
    }

    # Save
    print("\n[4/4] Saving output...")

    with open(GAZETTEERS_DIR / "nombres_arcaicos.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"    Saved: {GAZETTEERS_DIR / 'nombres_arcaicos.json'}")

    with open(GAZETTEERS_DIR / "nombres_arcaicos_flat.json", "w", encoding="utf-8") as f:
        json.dump(flat_names, f, ensure_ascii=False, indent=2)
    print(f"    Saved: {GAZETTEERS_DIR / 'nombres_arcaicos_flat.json'}")

    # Summary
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"Nombres arcaicos hombres: {len(unique_hombres)}")
    print(f"Nombres arcaicos mujeres: {len(unique_mujeres)}")
    print(f"Total nombres únicos: {len(unique_hombres) + len(unique_mujeres)}")
    print(f"Combinaciones generadas: {len(generated_names)}")

    print("\n10 Ejemplos aleatorios:")
    for ex in random.sample(generated_names, min(10, len(generated_names))):
        print(f"  • {ex['texto']}")


if __name__ == "__main__":
    main()
