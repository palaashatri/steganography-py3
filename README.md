# Python 3 Image Steganography

CLI tool for LSB image steganography with optional AES-256-GCM protection, fixed headers, and capacity checks.

## Folder Structure
| Folder | Description |
|---|---|
| 1_Implementation | All code |
| 2_ImagesAndVideos | Screenshots and demo video |

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Methods
- **lsb:** Basic sequential LSB substitution.
- **lsb-prng:** Pixels selected via PRNG permutation using `--prng-key`.
- **lsb-match-prng:** LSB matching (±1) with PRNG permutation.

Use lossless formats (PNG) for outputs; JPEG recompression will destroy hidden data.

## Usage

Encode a message into an image (basic LSB):
```bash
python 1_Implementation/app.py encode --image cover.png --out secret.png --message "hello world" --method lsb
```

Encode with PRNG permutation:
```bash
python 1_Implementation/app.py encode --image cover.png --out secret.png --message "hello world" --method lsb-prng --prng-key "my-key"
```

Encode with LSB matching + PRNG:
```bash
python 1_Implementation/app.py encode --image cover.png --out secret.png --message "hello world" --method lsb-match-prng --prng-key "my-key"
```

Optional encryption:
```bash
python 1_Implementation/app.py encode --image cover.png --out secret.png --in-file notes.txt --password "strong passphrase"
```

Decode to stdout (basic LSB):
```bash
python 1_Implementation/app.py decode --image secret.png --method lsb
```

Decode (PRNG-based):
```bash
python 1_Implementation/app.py decode --image secret.png --method lsb-prng --prng-key "my-key"
# or for LSB matching
python 1_Implementation/app.py decode --image secret.png --method lsb-match-prng --prng-key "my-key"
```

Decode to a file:
```bash
python 1_Implementation/app.py decode --image secret.png --out recovered.bin --method lsb
```

Add `--verbose` to see debug logging.

## Run script (macOS)
```bash
./run.sh encode --image cover.png --out secret.png --message "hi" --method lsb
./run.sh decode --image secret.png --method lsb
```

## Resources
* Steganography - [Wikipedia](https://en.wikipedia.org/wiki/Steganography)
* Python Image Library (Pillow) - [Website](https://python-pillow.org/)
