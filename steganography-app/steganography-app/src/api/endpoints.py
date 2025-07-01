from flask import Blueprint, request, jsonify
from core.steganography import Steganography
from core.encryption import Encryption
from utils.file_utils import save_file, read_file

api = Blueprint('api', __name__)

@api.route('/embed', methods=['POST'])
def embed_data():
    data = request.json
    image_path = data.get('image_path')
    secret_data = data.get('secret_data')
    password = data.get('password')

    if not image_path or not secret_data:
        return jsonify({'error': 'Image path and secret data are required.'}), 400

    # Encrypt the secret data
    encrypted_data = Encryption.encrypt(secret_data, password)

    # Embed the encrypted data into the image
    steganography = Steganography()
    result_image_path = steganography.embed(image_path, encrypted_data)

    return jsonify({'result_image_path': result_image_path}), 200

@api.route('/extract', methods=['POST'])
def extract_data():
    data = request.json
    image_path = data.get('image_path')
    password = data.get('password')

    if not image_path:
        return jsonify({'error': 'Image path is required.'}), 400

    # Extract the encrypted data from the image
    steganography = Steganography()
    encrypted_data = steganography.extract(image_path)

    # Decrypt the data
    secret_data = Encryption.decrypt(encrypted_data, password)

    return jsonify({'secret_data': secret_data}), 200

@api.route('/batch_process', methods=['POST'])
def batch_process():
    files = request.files.getlist('files')
    results = []

    for file in files:
        # Process each file (e.g., embed or extract data)
        # This is a placeholder for batch processing logic
        results.append({'file_name': file.filename, 'status': 'processed'})

    return jsonify({'results': results}), 200

@api.route('/cloud_integration', methods=['POST'])
def cloud_integration():
    # Placeholder for cloud integration logic
    return jsonify({'message': 'Cloud integration not implemented yet.'}), 501