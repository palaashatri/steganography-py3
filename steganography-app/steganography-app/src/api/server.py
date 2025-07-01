from flask import Flask, request, jsonify
from src.core import steganography, encryption, compression, validation
from src.utils.crypto_utils import derive_key
import threading

app = Flask(__name__)

@app.route('/encode', methods=['POST'])
def encode():
    data = request.json
    image_path = data.get('image_path')
    secret_message = data.get('secret_message')
    password = data.get('password')

    if not validation.validate_image(image_path) or not secret_message:
        return jsonify({'error': 'Invalid input'}), 400

    key = derive_key(password)
    encoded_image = steganography.embed_data(image_path, secret_message, key)

    return jsonify({'encoded_image_path': encoded_image}), 200

@app.route('/decode', methods=['POST'])
def decode():
    data = request.json
    encoded_image_path = data.get('encoded_image_path')
    password = data.get('password')

    if not validation.validate_image(encoded_image_path):
        return jsonify({'error': 'Invalid input'}), 400

    key = derive_key(password)
    secret_message = steganography.extract_data(encoded_image_path, key)

    return jsonify({'secret_message': secret_message}), 200

def run_server():
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    server_thread = threading.Thread(target=run_server)
    server_thread.start()