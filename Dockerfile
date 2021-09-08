FROM python:3.9-slim-buster
WORKDIR /app
RUN apt -qq update && apt -qq upgrade -y && \
    apt -qq install -y libzbar0
COPY requirements.txt requirements.txt
RUN pip3 install -U -r requirements.txt
COPY . .
CMD [ "python3", "-m" "alisu"]
