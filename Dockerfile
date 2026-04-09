FROM python:slim

# Python best practices for docker
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Add custom user sage inside the containr
RUN useradd -m sage

ENV APP_DIR=/sage
RUN mkdir -p $APP_DIR && chown sage:sage $APP_DIR
WORKDIR $APP_DIR

# Copy req and install python modules
COPY requirements.txt .
RUN pip install --no-cache-dir -r ./requirements.txt

# Copy the main code and setup correct ownership
COPY --chown=sage:sage app ./app
COPY --chown=sage:sage sage.py config.py docker-startup.sh ./
RUN chmod a+x $APP_DIR/docker-startup.sh

# Inform flask of the application instance
ENV FLASK_APP=sage.py

# Switch to non-root user
USER sage

EXPOSE 3110
ENTRYPOINT ["./docker-startup.sh"]