docker build -t cloze-dev-image .
docker tag cloze-dev-image jomof/cloze-dev-image:latest
docker push jomof/cloze-dev-image:latest