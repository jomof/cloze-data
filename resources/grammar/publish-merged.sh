export source=$(realpath $2)
export destination=$3
sudo rm -rf $destination
cp -r $source $destination