FROM python:3

ENV PYTHONUNBUFFERED=1

COPY . /app/
WORKDIR /app
# Install as editable so we don't keep two copies
RUN pip install -e .[server]

USER www-data
EXPOSE 8080
VOLUME /data/

# Allow loading custom_config.py from a volume
# This may have security implications that are, however, outside of my threat model
ENV PYTHONPATH="/data"

ENTRYPOINT ["/app/docker_entrypoint.sh", "house_inventory.wsgi:application"]
CMD ["-w", "4", "-b", "0.0.0.0:8080"]