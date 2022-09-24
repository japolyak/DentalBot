FROM python:3

WORKDIR /usr/src/app

RUN apt install libmariadb3 libmariadb-dev

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./main.py" ]