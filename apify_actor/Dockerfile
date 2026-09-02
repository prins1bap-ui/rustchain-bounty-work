FROM apify/actor-python:3.13

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./
RUN cat src/scanner_parts/part1.part src/scanner_parts/part2.part src/scanner_parts/part3.part src/scanner_parts/part4.part > src/scanner.py
CMD ["python", "-m", "src"]
