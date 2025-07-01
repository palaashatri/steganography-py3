import pywt

class DWTSteganography:
    def __init__(self):
        pass

    def embed(self, image, secret_data):
        coeffs = pywt.dwt2(image, 'haar')
        cA, (cH, cV, cD) = coeffs
        
        # Convert secret data to binary
        binary_data = ''.join(format(ord(i), '08b') for i in secret_data)
        data_len = len(binary_data)
        
        # Embed data into the horizontal coefficients
        for i in range(min(data_len, len(cH.flatten()))):
            flat_idx = i % len(cH.flatten())
            row, col = divmod(flat_idx, cH.shape[1])
            if row < cH.shape[0]:
                cH[row, col] = (cH[row, col] & ~1) | int(binary_data[i])
        
        return pywt.idwt2((cA, (cH, cV, cD)), 'haar')

    def extract(self, image):
        coeffs = pywt.dwt2(image, 'haar')
        _, (cH, _, _) = coeffs
        
        # Extract the embedded data from horizontal coefficients
        binary_data = ''
        for i in range(len(cH.flatten())):
            row, col = divmod(i, cH.shape[1])
            if row < cH.shape[0]:
                binary_data += str(int(cH[row, col]) & 1)
        
        # Convert binary data to string
        secret_data = ''.join(chr(int(binary_data[i:i + 8], 2)) for i in range(0, len(binary_data), 8))
        return secret_data.rstrip('\x00')  # Remove padding if any

    def get_capacity(self, image):
        """
        Calculate the maximum capacity for DWT steganography
        Args:
            image: numpy array
        Returns:
            Maximum bytes that can be embedded
        """
        # DWT capacity is more limited than LSB
        # We embed in the horizontal detail coefficients
        if len(image.shape) == 3:
            height, width, channels = image.shape
        else:
            height, width = image.shape
            channels = 1
        
        # DWT decomposes into 4 subbands, each 1/4 the size
        # We use the horizontal detail coefficients
        detail_size = (height // 2) * (width // 2)
        
        # Conservative estimate - we can embed in detail coefficients
        usable_bits = detail_size * channels
        
        return max(0, usable_bits // 8)  # Convert to bytes