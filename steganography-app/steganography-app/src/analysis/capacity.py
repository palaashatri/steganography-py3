def calculate_capacity(image):
    """
    Calculate the capacity of the image for data embedding.

    Parameters:
    image (PIL.Image): The input image for capacity analysis.

    Returns:
    int: The maximum number of bits that can be embedded in the image.
    """
    width, height = image.size
    # Assuming we can use the least significant bit of each pixel
    capacity = width * height * 3  # 3 for RGB channels
    return capacity

def analyze_capacity(image_path):
    """
    Analyze the capacity of the image located at the given path.

    Parameters:
    image_path (str): The path to the image file.

    Returns:
    dict: A dictionary containing the image capacity and other relevant metrics.
    """
    from PIL import Image

    try:
        image = Image.open(image_path)
        capacity = calculate_capacity(image)
        return {
            'image_path': image_path,
            'capacity': capacity,
            'width': image.width,
            'height': image.height,
            'mode': image.mode
        }
    except Exception as e:
        return {
            'error': str(e)
        }