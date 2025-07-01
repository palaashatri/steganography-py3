from PIL import Image
import io
import zlib

class Compression:
    @staticmethod
    def compress(data: bytes) -> bytes:
        """Compresses the input data using zlib."""
        return zlib.compress(data)

    @staticmethod
    def decompress(data: bytes) -> bytes:
        """Decompresses the input data using zlib."""
        return zlib.decompress(data)

    @staticmethod
    def compress_image(image: Image) -> bytes:
        """Compresses an image and returns the compressed byte data."""
        with io.BytesIO() as output:
            image.save(output, format='JPEG', quality=85)
            return output.getvalue()

    @staticmethod
    def decompress_image(data: bytes) -> Image:
        """Decompresses byte data back into an image."""
        with io.BytesIO(data) as input_stream:
            return Image.open(input_stream)