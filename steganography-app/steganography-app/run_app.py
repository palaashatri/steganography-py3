#!/usr/bin/env python3
"""
steganography-py3 GUI - Main Application Launcher
================================================

This is the main entry point for the steganography-py3 GUI.
It provides multiple ways to run the application:
1. GUI Mode (default) - Full-featured PyQt5 interface
2. CLI Mode - Command-line interface for batch operations
3. API Mode - REST API server for remote operations

Usage:
    python run_app.py                    # Start GUI
    python run_app.py --mode cli         # Start CLI
    python run_app.py --mode api         # Start API server
    python run_app.py --help             # Show help
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Add src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

def setup_logging(log_level="INFO"):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('steganography_app.log')
        ]
    )

def run_gui():
    """Launch the GUI application"""
    try:
        from PyQt5.QtWidgets import QApplication
        from gui.main_window import MainWindow
        
        app = QApplication(sys.argv)
        app.setApplicationName("steganography-py3 GUI")
        app.setApplicationVersion("2.0")
        
        # Set application style
        app.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
                background-color: white;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #e1e1e1;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #0078d4;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
        """)
        
        window = MainWindow()
        window.show()
        
        logging.info("GUI application started successfully")
        return app.exec_()
        
    except ImportError as e:
        print(f"Error: Could not import required GUI components: {e}")
        print("Make sure PyQt5 is installed: pip install PyQt5")
        return 1
    except (RuntimeError, ValueError) as e:
        logging.error("Failed to start GUI: %s", str(e))
        return 1

def run_cli():
    """Launch the CLI application"""
    print("steganography-py3 GUI - CLI Mode")
    print("=" * 50)
    
    try:
        # Import CLI components
        from core.steganography import SteganographyEngine
        
        engine = SteganographyEngine()
        print("CLI mode loaded successfully")
        print("Available commands:")
        print("  encode - Encode a message into an image")
        print("  decode - Decode a message from an image")
        print("  analyze - Analyze image quality metrics")
        print("  capacity - Calculate image capacity")
        print("  quit - Exit the application")
        
        while True:
            try:
                command = input("\nEnter command: ").strip().lower()
                
                if command == "quit":
                    break
                elif command == "encode":
                    cli_encode(engine)
                elif command == "decode":
                    cli_decode(engine)
                elif command == "analyze":
                    cli_analyze()
                elif command == "capacity":
                    cli_capacity()
                else:
                    print("Unknown command. Type 'quit' to exit.")
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except (ImportError, RuntimeError) as e:
                print(f"Error: {e}")
        
        return 0
        
    except (ImportError, RuntimeError) as e:
        logging.error("Failed to start CLI: %s", str(e))
        return 1

def cli_encode(engine):
    """CLI encode functionality"""
    try:
        image_path = input("Enter image path: ")
        message = input("Enter message to encode: ")
        password = input("Enter password (optional): ")
        algorithm = input("Enter algorithm (LSB/DCT/DWT/Adaptive LSB) [LSB]: ") or "LSB"
        output_path = input("Enter output path: ")
        
        print("Encoding...")
        result = engine.encode_sync(
            image_path=image_path,
            message=message,
            password=password,
            algorithm=algorithm,
            output_path=output_path
        )
        
        if result.get('success'):
            print(f"✓ Message encoded successfully to {output_path}")
            if 'metrics' in result:
                print(f"  PSNR: {result['metrics'].get('psnr', 'N/A'):.2f} dB")
                print(f"  SSIM: {result['metrics'].get('ssim', 'N/A'):.4f}")
        else:
            print(f"✗ Encoding failed: {result.get('error', 'Unknown error')}")
            
    except (ValueError, FileNotFoundError) as e:
        print(f"Error in encoding: {e}")

def cli_decode(engine):
    """CLI decode functionality"""
    try:
        image_path = input("Enter steganographic image path: ")
        password = input("Enter password (if encrypted): ")
        algorithm = input("Enter algorithm (LSB/DCT/DWT/Adaptive LSB) [LSB]: ") or "LSB"
        
        print("Decoding...")
        result = engine.decode_sync(
            image_path=image_path,
            password=password,
            algorithm=algorithm
        )
        
        if result.get('success'):
            print("✓ Message decoded successfully:")
            print(f"  Message: {result.get('message', 'N/A')}")
        else:
            print(f"✗ Decoding failed: {result.get('error', 'Unknown error')}")
            
    except (ValueError, FileNotFoundError) as e:
        print(f"Error in decoding: {e}")

def cli_analyze():
    """CLI analysis functionality"""
    try:
        from analysis.quality_metrics import QualityAnalyzer
        from utils.image_utils import ImageProcessor
        
        original_path = input("Enter original image path: ")
        stego_path = input("Enter steganographic image path: ")
        
        analyzer = QualityAnalyzer()
        processor = ImageProcessor()
        
        original = processor.load_image(original_path)
        stego = processor.load_image(stego_path)
        
        if original is None or stego is None:
            print("Error: Could not load images")
            return
        
        print("Analyzing...")
        metrics = analyzer.analyze_quality(original, stego)
        
        print("Quality Analysis Results:")
        print(f"  PSNR: {metrics.get('psnr', 'N/A'):.2f} dB")
        print(f"  SSIM: {metrics.get('ssim', 'N/A'):.4f}")
        print(f"  MSE: {metrics.get('mse', 'N/A'):.2f}")
        print(f"  Quality Score: {metrics.get('quality_score', 'N/A')}")
        
    except (ValueError, ImportError) as e:
        print(f"Error in analysis: {e}")

def cli_capacity():
    """CLI capacity calculation"""
    try:
        from utils.image_utils import ImageProcessor
        
        image_path = input("Enter image path: ")
        algorithm = input("Enter algorithm (LSB/DCT/DWT/Adaptive LSB) [LSB]: ") or "LSB"
        
        processor = ImageProcessor()
        capacity = processor.get_image_capacity(image_path, algorithm)
        
        print("Image Capacity Analysis:")
        print(f"  Algorithm: {algorithm}")
        print(f"  Capacity: {capacity} bytes ({capacity * 8} bits)")
        print(f"  Approximate characters: {capacity}")
        
    except (ValueError, FileNotFoundError) as e:
        print(f"Error calculating capacity: {e}")

def run_api():
    """Launch the API server"""
    try:
        from api.server import app
        print("Starting API server...")
        print("Server will be available at http://localhost:5000")
        print("API endpoints:")
        print("  POST /encode - Encode message into image")
        print("  POST /decode - Decode message from image") 
        print("  POST /analyze - Analyze image quality")
        print("  GET /capacity - Calculate image capacity")
        
        app.run(host='0.0.0.0', port=5000, debug=False)
        return 0
        
    except (ImportError, RuntimeError) as e:
        logging.error("Failed to start API server: %s", str(e))
        return 1

def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(
        description="steganography-py3 GUI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--mode', 
        choices=['gui', 'cli', 'api'], 
        default='gui',
        help='Application mode (default: gui)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='steganography-py3 GUI'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Check dependencies
    try:
        import numpy  # noqa: F401
        import PIL  # noqa: F401
        from cryptography.fernet import Fernet  # noqa: F401
    except ImportError as e:
        print(f"Error: Missing required dependency: {e}")
        print("Please install dependencies: pip install -r requirements.txt")
        return 1
    
    # Run application in specified mode
    if args.mode == 'gui':
        return run_gui()
    elif args.mode == 'cli':
        return run_cli()
    elif args.mode == 'api':
        return run_api()
    else:
        print(f"Unknown mode: {args.mode}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
