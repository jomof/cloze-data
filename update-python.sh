bazel run //:requirements.update
bazel run //:gazelle_python_manifest.update
bazel run //:gazelle update
buildifier --lint=fix -r .
