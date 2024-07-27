# Use an existing base image
FROM mcr.microsoft.com/devcontainers/universal:2

# Update package lists using apt-get
RUN apt-get update && apt-get install -y \
    apt-transport-https ca-certificates gnupg curl 

RUN curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg

RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list

RUN sudo apt-get update

RUN sudo apt-get install -y google-cloud-cli google-cloud-cli-firestore-emulator

RUN sudo sudo apt-get install -y google-cloud-cli-datastore-emulator

RUN rm -rf /var/lib/apt/lists/*

RUN npm install -g nodemon
RUN npm install -g @bazel/bazelisk
RUN go install github.com/bazelbuild/buildtools/buildifier@latest
RUN npm install -g @bazel/ibazel

RUN pip install mecab-python3==1.0.9
RUN pip install unidic==1.1.0
RUN python -m unidic download

RUN pip3 install --upgrade --user google-cloud-aiplatform

RUN sudo gcloud config set project jomof-sandbox
RUN gcloud config set project "jomof-sandbox"

ENV DATASTORE_DATASET=jomof-sandbox
ENV DATASTORE_EMULATOR_HOST=127.0.0.1:3002
ENV DATASTORE_EMULATOR_HOST_PATH=127.0.0.1:3002/datastore
ENV DATASTORE_HOST=http://127.0.0.1:3002
ENV DATASTORE_PROJECT_ID=jomof-sandbox

# Set default command to run when container starts
CMD ["/bin/bash"]