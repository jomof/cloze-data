mkdir sample
ls all | shuf -n 5 | xargs -I{} cp "all/{}" "sample/"