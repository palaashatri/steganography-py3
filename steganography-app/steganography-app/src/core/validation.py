def validate_image_format(file_path):
    valid_formats = ['.png', '.jpg', '.jpeg', '.bmp']
    if not any(file_path.endswith(ext) for ext in valid_formats):
        raise ValueError("Invalid image format. Supported formats are: PNG, JPG, JPEG, BMP.")

def validate_data_integrity(original_data, extracted_data):
    if original_data != extracted_data:
        raise ValueError("Data integrity check failed. The extracted data does not match the original data.")

def validate_file_size(file_path, max_size):
    import os
    file_size = os.path.getsize(file_path)
    if file_size > max_size:
        raise ValueError(f"File size exceeds the maximum limit of {max_size} bytes.")