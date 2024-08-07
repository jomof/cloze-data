# Use an existing base image
FROM us-west1-docker.pkg.dev/cloud-workstations-images/predefined/code-oss:latest

RUN npm install -g @bazel/bazelisk
RUN go install github.com/bazelbuild/buildtools/buildifier@latest
RUN npm install -g @bazel/ibazel

RUN pip install mecab-python3==1.0.9
RUN pip install unidic==1.1.0

RUN sudo python -m unidic download

RUN git config --global user.email "jomofisher@gmail.com"
RUN git config --global user.name "Jomo Fisher"

CMD ["/google/scripts/entrypoint.sh"]
