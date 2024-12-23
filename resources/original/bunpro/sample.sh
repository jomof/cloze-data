cd /workspaces/cloze-data/resources/original/bunpro
mkdir -p sample
ls all | shuf -n 60 | xargs -I{} cp "all/{}" "sample/"