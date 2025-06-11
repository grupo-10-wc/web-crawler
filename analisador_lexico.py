import re
import Levenshtein

GOOD_KEYWORDS = {
    "redução", "beneficio", "economia", "energia renovável", "sustentabilidade",
    "eficiência energética", "tecnologia limpa", "inovação", "descarbonização",
    "soluções verdes", "investimento", "crescimento", "desenvolvimento", "oportunidade", "progresso",
    "incentivo", "conscientização", "eficiência", "desconto", "tarifa social",
    "bandeira verde", "energia solar", "energia eólica", "hidrelétrica", "economia de energia",
    "otimização", "modernização", "smart grid", "medidor inteligente", "automação",
    "sustentável", "ecológico", "limpo", "renovável", "verde", "eficiente",
    "poupança", "redução de custos", "menor consumo", "baixo custo", "gratuito",
    "subvenção", "subsídio", "financiamento", "crédito", "facilidade", "melhoria",
    "upgrade", "atualização", "tecnologia avançada", "solução", "benefício tarifário"
}


BAD_KEYWORDS = {
    "aumento", "elevação", "alta", "subida", "majoração", "reajuste",
    "desperdício", "gasto excessivo", "consumo alto",
    "sobrecarga", "pico de consumo", "vermelha",
    "multa", "penalidade", "taxa adicional", "cobrança extra",
    "energia suja", "poluição", "emissão", "carbono", "combustível fóssil",
    "desperdício energético", "perda", "vazamento", "má utilização",
    "obsoleto", "ultrapassado", "ineficiente", "antigo", "defasado",
    "custoso", "oneroso", "dispendioso", "alto custo",
    "fatura elevada", "débito", "inadimplência",
    "corte", "suspensão", "interrupção", "desligamento",
    "problema", "falha", "defeito", "avaria", "mau funcionamento",
    "despesas", "gastos", "custos elevados", "preço alto", "manunteção", ""
}

ALL_KEYWORDS = GOOD_KEYWORDS.union(BAD_KEYWORDS)

def tokenize(text: str):
    return re.findall(r"\b\w+\b", text.lower())

def classify_tokens(tokens: list[str], link: str, threshold: float = 0.8):
    good = []
    bad = []
    token_counts = {}

    for token in tokens:
        # Check if the token is in any of the keyword lists
        for keyword in ALL_KEYWORDS:
            similarity = Levenshtein.ratio(token, keyword)
            if similarity >= threshold:
                # Count the token occurrences
                token_counts[token] = token_counts.get(token, 0) + 1
                if keyword in GOOD_KEYWORDS:
                    good.append((token, keyword, similarity, link))
                elif keyword in BAD_KEYWORDS:
                    bad.append((token, keyword, similarity, link))
                break  # Avoid double classification
    return token_counts, good, bad
