FROM python:3.8.5-slim
COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./
CMD streamlit run app/app.py --server.port $PORT