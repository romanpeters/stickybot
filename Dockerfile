FROM python:3.7

ADD . /bot
WORKDIR /bot
RUN sed -i -e 's/# nl_NL.UTF-8 UTF-8/nl_NL.UTF-8 UTF-8/' /etc/locale.gen && locale-gen
RUN pip install --no-cache-dir -U -r requirements.txt

CMD ["python", "-u", "bot.py"]