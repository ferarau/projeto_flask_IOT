import os
import json
import psycopg2
import paho.mqtt.client as mqtt
from psycopg2.extras import RealDictCursor
from flask import Flask, jsonify

app = Flask(__name__)

# String de conexão do Neon (com fallback para uso local)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://neondb_owner:npg_GLjWDmA36aUv@ep-cool-sunset-b477wxcp-pooler.c-6.us-east-2.aws.neon.tech/neondb?sslmode=require"
)

# Configurações MQTT
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "projeto/caixadagua/sensor"


def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def salvar_leitura_db(distancia, alerta):
    if not isinstance(distancia, (int, float)) or distancia < 0:
        raise ValueError("Distância inválida")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO leituras (distancia, alerta) VALUES (%s, %s) RETURNING id;",
        (distancia, alerta)
    )
    novo_id = cur.fetchone()['id']
    conn.commit()
    cur.close()
    conn.close()
    return novo_id


# Callbacks do MQTT (Compatível com Paho-MQTT v2)
def on_connect(client, userdata, flags, rc, properties=None):
    print(f"Conectado ao Broker MQTT com código: {rc}")
    client.subscribe(MQTT_TOPIC)


def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        distancia = float(data.get("distancia"))
        alerta = bool(data.get("alerta"))

        salvar_leitura_db(distancia, alerta)
        print(f"[MQTT] Dado salvo no banco: Distância={distancia}cm | Alerta={alerta}")
    except Exception as e:
        print(f"[MQTT Erro] Falha ao processar mensagem: {e}")


# Inicialização do Cliente MQTT (Executa apenas localmente, sem travar a Vercel)
if not os.getenv("VERCEL"):
    try:
        mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
    except Exception as e:
        print(f"Erro ao conectar no MQTT: {e}")


# Rotas da API Flask
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "API IoT Online",
        "projeto": "Monitoramento Caixa d'Água"
    }), 200


@app.route("/api/dados", methods=["GET"])
def obter_dados():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, distancia, alerta, data_hora FROM leituras ORDER BY data_hora DESC LIMIT 50;")
        leituras = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(leituras), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)