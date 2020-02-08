FROM python:3.7

ADD . /bot
WORKDIR /bot
RUN apt-get update && apt-get -y install locales \
 && sed -i -e 's/# nl_NL.UTF-8 UTF-8/nl_NL.UTF-8 UTF-8/' /etc/locale.gen && locale-gen \
 && pip install --no-cache-dir -U -r requirements.txt

CMD ["python", "-u", "bot.py"]