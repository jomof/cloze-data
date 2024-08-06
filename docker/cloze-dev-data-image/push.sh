docker build -t cloze-dev-data-image .
docker tag cloze-dev-data-image jomof/cloze-dev-data-image:latest
docker push jomof/cloze-dev-data-image:latest