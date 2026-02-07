# Clarity

Clarity is an article credibility analyzer with:
- Flask backend API (`/api/analyze/url`, `/api/analyze/text`, `/api/analyze/pdf`)
- Static frontend served by Flask

## Run with Docker (recommended)

1. Export your Dedalus key in the shell:

```bash
export DEDALUS_API_KEY="your_key_here"
```

2. Build and run (from the project root):

```bash
cd <path-to-clarity>
docker compose up --build
```

3. Open:

- http://localhost:5001

4. Stop:

```bash
docker compose down
```

## End-to-end test checklist

1. Health endpoint:

```bash
curl http://localhost:5001/api/health
```

Expect `{"status":"ok","dedalus_api_key_loaded":true}`.

2. URL analysis:
- Open http://localhost:5001
- Paste one article URL
- Click `Analyze Article`
- Confirm redirect to `results.html` with populated scores

3. PDF analysis:
- Upload a `.pdf` using the file picker
- Confirm filename appears in the upload box
- Click `Analyze Article`
- Confirm results page loads

## Run without Docker

```bash
cd <path-to-clarity>/backend
PORT=5001 python3 app.py
```

Then open http://localhost:5001
