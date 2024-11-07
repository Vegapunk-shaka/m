FROM 5hojib/vegapunk:latest
WORKDIR /usr/src/mergebot
RUN chmod 777 /usr/src/mergebot
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x start.sh

CMD ["bash","start.sh"]
