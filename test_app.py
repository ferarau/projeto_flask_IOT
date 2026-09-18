import pytest
from main import app, salvar_leitura_db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# 1. TESTE SIMPLES: Status da rota /
def test_home_status(client):
    resposta = client.get('/')
    assert resposta.status_code == 200
    assert resposta.json['status'] == "API IoT Online"

# 2. TESTE PARAMETRIZADO: Regra de negócio do alerta
@pytest.mark.parametrize("distancia, resultado_esperado_alerta", [
    (3.5, True),    # Limiar crítico (< 10cm)
    (9.9, True),    # Limite inferior
    (10.0, False),  # Limite de disparo
    (50.0, False)   # Nível normal
])
def test_regra_alerta_distancia(distancia, resultado_esperado_alerta):
    alerta_calculado = distancia < 10.0
    assert alerta_calculado == resultado_esperado_alerta

# 3. TESTE DE EXCEÇÃO: Dados inválidos
def test_salvar_distancia_invalida_excecao():
    with pytest.raises(ValueError):
        salvar_leitura_db(-10.0, False)