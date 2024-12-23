cd /workspaces/cloze-data/resources/original/bunpro
mkdir -p sample
ls all | shuf -n 1000 | xargs -I{} cp "all/{}" "sample/"