FROM datasetteproject/datasette AS build
WORKDIR /app
COPY import-wtr.py .
COPY data ./data
RUN pip install python-dateutil
RUN python3 ./import-wtr.py
RUN datasette inspect wtr.db --inspect-file inspect-data.json --load-extension=/usr/local/lib/mod_spatialite.so

FROM datasetteproject/datasette
WORKDIR /app

COPY --from=build /app/wtr.db .
COPY --from=build /app/inspect-data.json .
COPY templates ./templates
COPY static ./static

EXPOSE 8001
CMD ["datasette", "serve", \
	"./wtr.db", "--host", "0.0.0.0", "--port", "8001", \
	"--load-extension=/usr/local/lib/mod_spatialite.so", \
	"--template-dir", "./templates", \
	"--static=static:./static", \
	"--inspect-file", "./inspect-data.json"]
