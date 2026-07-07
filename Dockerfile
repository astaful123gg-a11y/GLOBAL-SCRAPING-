FROM searxng/searxng:latest

# Copy custom settings that enable JSON API
COPY settings.yml /etc/searxng/settings.yml

EXPOSE 8080
