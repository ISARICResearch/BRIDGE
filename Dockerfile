FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
# Compile requirements.txt from pyproject.toml using pip-tools
RUN pip install --no-cache-dir pip-tools && \
    pip-compile --output-file=requirements.txt pyproject.toml
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Install the package itself without re-resolving dependencies
RUN pip install --no-cache-dir --no-deps .

EXPOSE 8050

CMD ["gunicorn", "--bind", "0.0.0.0:8050", "app:server"]
