import os
import json
import logging
import joblib
from flask import Flask, request, jsonify

# Настраиваем структурированное JSON-логирование для ELK-стека
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}'
)
logger = logging.getLogger("ml_credit_service")

app = Flask(__name__)

# Поиск пути к моделям динамически относительно корня проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_model(version='v1'):
    model_path = os.path.join(BASE_DIR, "models", f"model_{version}.joblib")
    if os.path.exists(model_path):
        return joblib.load(model_path)
    return None

# Эндпоинт GET /health — проверка работоспособности сервиса
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "credit_card_default_pred"}), 200

# Эндпоинт POST /predict — принимает JSON с признаками клиента, возвращает прогноз и вероятность
@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json(force=True)
        if not data or 'features' not in data:
            return jsonify({"error": "invalid request, missing 'features' key"}), 400
            
        features = data['features']
        
        # Получаем версию модели из query-параметров 
        version = request.args.get('version', 'v1')
        model = load_model(version)
        
        if model is None:
            return jsonify({"error": f"model version '{version}' not found"}), 404
            
        # Заворачиваем в список, если передан один вектор признаков
        input_data = [features] if not isinstance(features[0], list) else features
        
        prediction = model.predict(input_data)[0]
        probability = model.predict_proba(input_data)[0][1]
        
        # Запись структурированного лога в stdout
        log_payload = {
            "event": "inference",
            "model_version": version,
            "prediction": int(prediction),
            "probability": float(probability)
        }
        logger.info(json.dumps(log_payload))
        
        return jsonify({
            "status": "success",
            "model_version": version,
            "prediction": int(prediction),
            "probability": float(probability)
        }), 200

    except Exception as e:
        logger.error(json.dumps({"event": "error", "details": str(e)}))
        return jsonify({"error": "internal server error", "details": str(e)}), 500

if __name__ == '__main__':
    # В production-like среде запускаем на 0.0.0.0, чтобы слушать внешние запросы
    app.run(host='0.0.0.0', port=5000)
