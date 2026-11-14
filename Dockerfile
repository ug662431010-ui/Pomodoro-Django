# CS50W Lecture 7 - Docker: describes the environment the app runs in
FROM python:3.13

WORKDIR /usr/src/app

# install the packages first, so Docker can cache this step
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000
# create the SQLite database if needed, then start the Django development server
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
