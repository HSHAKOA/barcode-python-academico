"""Configuração acadêmica demonstrativa (valores fictícios de exemplo).

ATENÇÃO: Os nomes de cores, capacidades e consumos por bip definidos neste arquivo
são estritamente FICTÍCIOS para fins didáticos e de validação em laboratório,
não representando parâmetros operacionais reais de linha industrial.
"""

# Máquinas demonstrativas cadastradas (chave = prefixo do código de barras)
MAQUINAS = {
    "M1": "Máquina 1",
    "M2": "Máquina 2",
    "M3": "Máquina 3",
    "M4": "Máquina 4",
}

# Quantidade base fictícia de resina Marfim consumida a cada bip/receita (kg)
MARFIM_KG_POR_BIP = 20.0

# Cores demonstrativas disponíveis para controle de estoque de Moído e Pigmento
CORES = ["Branco", "Cinza Claro", "Preto", "Azul"]

# Cor do cabeçalho das etiquetas PDF por cor da receita
CORES_HEX = {
    "Sem cor":      "#0984e3",
    "Branco":       "#7f8c8d",
    "Cinza Claro":  "#95a5a6",
    "Preto":        "#2c3e50",
    "Azul":         "#2980b9",
}

# Receitas demonstrativas: cada chave compõe o código {MAQUINA}-{RECEITA}
# moido_kg / pigmento_kg = consumo fictício adicional por bip (0.0 = não utiliza)
RECEITAS = {
    "PURO": {
        "nome": "Marfim Puro",
        "cor": "Sem cor",
        "moido_kg": 0.0,
        "pigmento_kg": 0.0,
    },
    "PIG-BR": {
        "nome": "Marfim + Pigmento",
        "cor": "Branco",
        "moido_kg": 0.0,
        "pigmento_kg": 0.5,
    },
    "PIG-CC": {
        "nome": "Marfim + Pigmento",
        "cor": "Cinza Claro",
        "moido_kg": 0.0,
        "pigmento_kg": 0.5,
    },
    "PIG-PT": {
        "nome": "Marfim + Pigmento",
        "cor": "Preto",
        "moido_kg": 0.0,
        "pigmento_kg": 0.5,
    },
    "PIG-AZ": {
        "nome": "Marfim + Pigmento",
        "cor": "Azul",
        "moido_kg": 0.0,
        "pigmento_kg": 0.5,
    },
    "MOI-BR": {
        "nome": "Marfim + Moído + Pigmento",
        "cor": "Branco",
        "moido_kg": 10.0,
        "pigmento_kg": 0.5,
    },
    "MOI-CC": {
        "nome": "Marfim + Moído + Pigmento",
        "cor": "Cinza Claro",
        "moido_kg": 10.0,
        "pigmento_kg": 0.5,
    },
    "MOI-PT": {
        "nome": "Marfim + Moído + Pigmento",
        "cor": "Preto",
        "moido_kg": 10.0,
        "pigmento_kg": 0.5,
    },
    "MOI-AZ": {
        "nome": "Marfim + Moído + Pigmento",
        "cor": "Azul",
        "moido_kg": 10.0,
        "pigmento_kg": 0.5,
    },
}
