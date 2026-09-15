# AlphaCrafter DeepSeek patch

From the server-side AlphaCrafter repository root, copy this patch over it:

```bash
cp -R /path/to/deepseek_patch/. /path/to/AlphaCrafter/
```

Configure the key without committing it:

```bash
cd /path/to/AlphaCrafter
cp .env.example .env
vim .env
```

Create and activate the environment:

```bash
python3.10 -m venv afc
source afc/bin/activate
python -m pip install --upgrade pip
pip install -e .
pip install openai python-dotenv pydantic requests pyyaml pandas numpy scikit-learn matplotlib seaborn tqdm lightgbm
```

Create an A-share session after applying the patch:

```bash
cp -R alphacrafter/sandbox/template_a alphacrafter/sandbox/repro-csi300
```

If the session already existed before applying the patch, update its model file:

```bash
cp alphacrafter/sandbox/template_a/config/models.json \
   alphacrafter/sandbox/repro-csi300/config/models.json
```

Run from the Python package directory:

```bash
cd alphacrafter
python main.py repro-csi300
```

The repository's current CLI uses a positional session ID. Do not use
`--session_id`. The included config intentionally sets `max_cycles: 1` for the
first test. Increase it after the pipeline completes successfully.
