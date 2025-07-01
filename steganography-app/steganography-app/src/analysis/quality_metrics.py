import numpy as np
from math import log10, sqrt
try:
    from skimage.measure import compare_ssim as ssim_func
    from skimage.measure import compare_psnr as psnr_func
except ImportError:
    # Fallback for newer scikit-image versions
    try:
        from skimage.metrics import structural_similarity as ssim_func
        from skimage.metrics import peak_signal_noise_ratio as psnr_func
    except ImportError:
        # If neither works, we'll use our custom implementations
        ssim_func = None
        psnr_func = None

def calculate_psnr(original_image, stego_image):
    mse = ((original_image - stego_image) ** 2).mean()
    if mse == 0:
        return float('inf')
    return 20 * log10(255.0 / sqrt(mse))

def calculate_ssim(original_image, stego_image):
    C1 = (0.01 * 255) ** 2
    C2 = (0.03 * 255) ** 2
    mu_x = original_image.mean()
    mu_y = stego_image.mean()
    sigma_x = original_image.var()
    sigma_y = stego_image.var()
    sigma_xy = ((original_image - mu_x) * (stego_image - mu_y)).mean()

    numerator = (2 * mu_x * mu_y + C1) * (2 * sigma_xy + C2)
    denominator = (mu_x ** 2 + mu_y ** 2 + C1) * (sigma_x + sigma_y + C2)
    return numerator / denominator

def calculate_quality_metrics(original_image, stego_image):
    psnr = calculate_psnr(original_image, stego_image)
    ssim = calculate_ssim(original_image, stego_image)
    return {
        'PSNR': psnr,
        'SSIM': ssim
    }

class QualityAnalyzer:
    """Quality analysis for steganographic images"""
    
    def __init__(self):
        pass
    
    def analyze_quality(self, original_image: np.ndarray, stego_image: np.ndarray) -> dict:
        """Comprehensive quality analysis between original and steganographic images"""
        results = {}
        
        try:
            # Ensure images are the same shape
            if original_image.shape != stego_image.shape:
                raise ValueError("Images must have the same dimensions")
            
            # Convert to grayscale if needed for some metrics
            if len(original_image.shape) == 3:
                orig_gray = np.mean(original_image, axis=2)
                stego_gray = np.mean(stego_image, axis=2)
            else:
                orig_gray = original_image
                stego_gray = stego_image
            
            # Calculate PSNR (Peak Signal-to-Noise Ratio)
            if psnr_func is not None:
                results['psnr'] = psnr_func(original_image, stego_image, data_range=255)
            else:
                results['psnr'] = calculate_psnr(original_image, stego_image)
            
            # Calculate SSIM (Structural Similarity Index)
            if len(original_image.shape) == 3:
                # For color images, calculate SSIM for each channel
                ssim_vals = []
                for i in range(original_image.shape[2]):
                    if ssim_func is not None:
                        ssim_val = ssim_func(original_image[:, :, i], stego_image[:, :, i], data_range=255)
                    else:
                        ssim_val = calculate_ssim(original_image[:, :, i], stego_image[:, :, i])
                    ssim_vals.append(ssim_val)
                results['ssim'] = np.mean(ssim_vals)
            else:
                if ssim_func is not None:
                    results['ssim'] = ssim_func(original_image, stego_image, data_range=255)
                else:
                    results['ssim'] = calculate_ssim(original_image, stego_image)
            
            # Calculate MSE (Mean Squared Error)
            results['mse'] = np.mean((original_image.astype(float) - stego_image.astype(float)) ** 2)
            
            # Calculate MAE (Mean Absolute Error)
            results['mae'] = np.mean(np.abs(original_image.astype(float) - stego_image.astype(float)))
            
            # Calculate histogram correlation
            results['histogram_correlation'] = self._calculate_histogram_correlation(original_image, stego_image)
            
            # Quality assessment
            results['quality_score'] = self._calculate_quality_score(results)
            
        except (ImportError, RuntimeError) as e:
            print(f"Error in quality analysis: {e}")
            results = {'error': str(e)}
        
        return results
    
    def _calculate_histogram_correlation(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """Calculate correlation between image histograms"""
        try:
            if len(img1.shape) == 3:
                # For color images, calculate correlation for each channel
                correlations = []
                for i in range(img1.shape[2]):
                    hist1, _ = np.histogram(img1[:, :, i], bins=256, range=(0, 256))
                    hist2, _ = np.histogram(img2[:, :, i], bins=256, range=(0, 256))
                    correlation = np.corrcoef(hist1, hist2)[0, 1]
                    if not np.isnan(correlation):
                        correlations.append(correlation)
                return np.mean(correlations) if correlations else 0.0
            else:
                hist1, _ = np.histogram(img1, bins=256, range=(0, 256))
                hist2, _ = np.histogram(img2, bins=256, range=(0, 256))
                correlation = np.corrcoef(hist1, hist2)[0, 1]
                return correlation if not np.isnan(correlation) else 0.0
        except (ValueError, ZeroDivisionError):
            return 0.0
    
    def _calculate_quality_score(self, metrics: dict) -> str:
        """Calculate overall quality assessment"""
        try:
            psnr_val = metrics.get('psnr', 0)
            ssim_val = metrics.get('ssim', 0)
            
            if psnr_val > 40 and ssim_val > 0.95:
                return "Excellent"
            elif psnr_val > 30 and ssim_val > 0.90:
                return "Good"
            elif psnr_val > 25 and ssim_val > 0.80:
                return "Fair"
            else:
                return "Poor"
        except (ValueError, KeyError):
            return "Unknown"
    
    def calculate_capacity(self, image_shape: tuple, algorithm: str = "LSB") -> int:
        """Calculate theoretical embedding capacity"""
        height, width = image_shape[:2]
        channels = image_shape[2] if len(image_shape) == 3 else 1
        
        if algorithm == "LSB":
            # 1 bit per pixel per channel
            return (height * width * channels) // 8  # Convert bits to bytes
        elif algorithm == "DCT":
            # Conservative estimate for DCT
            return (height * width) // 64
        elif algorithm == "DWT":
            # Conservative estimate for DWT
            return (height * width) // 32
        else:
            return (height * width) // 8
    
    def detect_steganography(self, image: np.ndarray) -> dict:
        """Simple steganography detection analysis"""
        results = {
            'suspicious_patterns': False,
            'lsb_analysis': 0.0,
            'histogram_analysis': 'normal',
            'confidence': 0.0
        }
        
        try:
            # LSB analysis - check for unusual patterns in least significant bits
            if len(image.shape) == 3:
                lsb_vals = []
                for i in range(image.shape[2]):
                    lsb = image[:, :, i] & 1
                    lsb_ratio = np.mean(lsb)
                    lsb_vals.append(abs(lsb_ratio - 0.5))
                results['lsb_analysis'] = np.mean(lsb_vals)
            else:
                lsb = image & 1
                results['lsb_analysis'] = abs(np.mean(lsb) - 0.5)
            
            # Simple threshold-based detection
            if results['lsb_analysis'] > 0.1:
                results['suspicious_patterns'] = True
                results['confidence'] = min(results['lsb_analysis'] * 2, 1.0)
            
        except (ValueError, IndexError) as e:
            results['error'] = str(e)
        
        return results