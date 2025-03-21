FROM python:3.10
WORKDIR /code
ADD . /code
RUN pip3 install --upgrade pip  # ✅ Correct
RUN pip3 install -r requirements.txt
COPY . /code
CMD ["python", "main.py"]






