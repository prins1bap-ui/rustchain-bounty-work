FROM apify/actor-python:3.13@sha256:c04163f4586c0aa8b1c8f8656beb456d0bd725fcc796b51c4197e8b51b206caa

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./
RUN cat src/scanner_parts/part1.part src/scanner_parts/part2.part src/scanner_parts/part3.part src/scanner_parts/part4.part > src/scanner.py \
    && rm -rf src/scanner_parts tests .pytest_cache
CMD ["python", "-m", "src"]
