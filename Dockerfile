FROM python:3.9

WORKDIR /usr/src/app

RUN apt install wget

RUN wget https://downloads.mariadb.com/MariaDB/mariadb_repo_setup

RUN echo "733cf126b03f73050e242102592658913d10829a5bf056ab77e7f864b3f8de1f  mariadb_repo_setup" \
    | sha256sum -c -

RUN chmod +x mariadb_repo_setup

RUN ./mariadb_repo_setup \
   --mariadb-server-version="mariadb-10.6"

RUN apt install -y libmariadb3 libmariadb-dev

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY bot/ bot/

CMD [ "python", "./main.py" ]
