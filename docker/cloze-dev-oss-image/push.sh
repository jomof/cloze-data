# gcloud auth configure-docker us-west1-docker.pkg.dev

docker build -t cloze-dev-oss-image .
docker tag cloze-dev-oss-image us-west1-docker.pkg.dev/jomof-sandbox/docker-repo/cloze-dev-oss-image:latest
docker push us-west1-docker.pkg.dev/jomof-sandbox/docker-repo/cloze-dev-oss-image:latest