# House inventory web app

I keep losing my stuff, so I decided to make myself an inventory web app using Django.

Here it is for your enjoyment.

## Features

- Based on the proven Django Admin web interface
- Nested locations
- Customizable location codes
    - i.e. Living room > Cabinet > 3rd drawer: `LR.CAB.D3`
- Item categories
- Batch operations:
    - Move multiple items into another location
    - Assign categories
    - Create "tabular" cabinet shelf locations
- Filtering by location, category
- Search
- Item expiration (though no reminders)

## Deploy with Docker

- Use the `docker-compose.yml` file found in this repo, or use the image
  `ghcr.io/depau/house_inventory:main `.
- Edit `volumes` and map `/data` to a local directory for persistent data storage
- Copy and edit `custom_settings.py.sample` to `custom_settings.py` into the data volume
  - Review all settings, pay particular attention to `SECRET_KEY`, `ALLOWED_HOSTS` and the
    entries related to Docker
- Launch the container with `docker-compose up -d`
- Create a super user account with `docker-compose exec app python manage.py createsuperuser`

Optional:

- Configure your reverse-proxy to serve static files directly from `VOL/static`. Be extra sure
  that you're not also serving your config and the SQLite database ;)

## License

GNU General Public License v3.0 or later.