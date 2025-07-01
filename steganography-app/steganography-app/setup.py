from setuptools import setup, find_packages

setup(
    name='steganography-app',
    version='0.1.0',
    author='Your Name',
    author_email='your.email@example.com',
    description='A steganography application with encryption and analysis features.',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'PyQt5>=5.15.0',
        'PyQt5-tools>=5.15.0',
        'Pillow>=9.0.0',
        'numpy>=1.21.0',
        'opencv-python>=4.5.0',
        'cryptography>=3.4.0',
        'scipy>=1.7.0',
        'scikit-image>=0.18.0',
        'matplotlib>=3.5.0',
        'flask>=2.0.0',
        'requests>=2.25.0',
        'psutil>=5.8.0',
        'pywavelets>=1.1.0',
        'numba>=0.56.0'
    ],
    entry_points={
        'console_scripts': [
            'steganography-app=main:main',  # Adjust according to your main function
        ],
    },
)