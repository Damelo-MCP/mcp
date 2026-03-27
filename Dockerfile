FROM python:3.13

COPY requirements.txt .

RUN pip install --upgrade pip && pip install -r requirements.txt
RUN pip install git+https://github.com/PrefectHQ/fastmcp.git@main

COPY . .

EXPOSE 8080

CMD ["uvicorn", "server:app", "--host", "0.0.0.0" ,"--port" ,"8080"]