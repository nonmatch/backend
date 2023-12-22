FROM python:3.11-bookworm
# Does not work with python 3.12 https://stackoverflow.com/a/77275009

RUN apt-get update && apt-get install -y build-essential python3-psycopg2 libpq-dev

COPY requirements.txt /opt/backend/
WORKDIR /opt/backend/
RUN pip3 install -r requirements.txt

COPY . /opt/backend/

EXPOSE 5000

CMD [ "flask", "run", "-h", "0.0.0.0", "--debug" ]