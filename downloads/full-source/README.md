# Signature Llama — Full Source Code

The complete Signature Llama implementation. Independent project — not affiliated with Meta.

## What's here

- **model.py** — the neural network model (transformer architecture)
- **tokenizer.py** — text tokenizer
- **train.py** — training script
- **export.py** — export trained weights
- **build_corpus.py** — training corpus builder
- **vocab.json** — vocabulary file
- **sigllama-v2.bin** — trained weights (v2, 4,056,768 parameters)

## Quick start

```python
from model import SignatureLlama
from tokenizer import Tokenizer
import numpy as np

# Load weights
weights = np.fromfile('sigllama-v2.bin', dtype=np.float32)

# Initialize
tok = Tokenizer('vocab.json')
model = SignatureLlama(weights)

# Generate
prompt = "Hello"
tokens = tok.encode(prompt)
output = model.generate(tokens, max_tokens=50)
print(tok.decode(output))
```

## Training your own

```bash
python3 build_corpus.py --input your_text.txt --output corpus.bin
python3 train.py --corpus corpus.bin --output my-llama.bin
```

Free to use. Built by the Signature system.
