bazel run //:requirements.update
bazel run //:gazelle_python_manifest.update
bazel run //:gazelle update
find . -name 'BUILD*' -o -name '*.bzl' -o -name 'WORKSPACE' -o -name '*.bazel' | xargs buildifier --lint=fix --warnings=all 

