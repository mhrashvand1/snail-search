# Snail Search

This project uses **[`uv`](https://docs.astral.sh/uv/)** as the Python package manager for fast and reliable dependency management.

## Installation

First, install **uv** by following the official guide:
👉 [https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/)

## Setting Up the Project

Install all dependencies:

```bash
uv sync
```

## Running the Project

Start the database service:

```bash
docker compose -f compose-local-infra.yml up -d
```

Activate the virtual environment:

```bash
# On Linux/macOS
source .venv/bin/activate

# On Windows
.venv\Scripts\activate
```

Populate the database (this step may take a few minutes):

```bash
python manage.py populate_db
```

Run the application:

```bash
python manage.py runserver
```


## 🐌 Your Mission

The search endpoint is **super slow right now — like a snail!**
It takes around **20 seconds** to return a response.

Your mission: **make it lightning fast ⚡ — under 1 second!**

Try it out here:

```
http://127.0.0.1:8000/api/search?q=inception
```



## Notes

- Improving search quality earns extra points. 

- You have complete freedom in choosing the technology to improve search speed and quality.

- Elasticsearch might be a good option.

