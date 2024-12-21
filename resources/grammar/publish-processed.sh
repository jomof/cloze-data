
#echo ---------------------
export TARGET=$1
#echo Target: $TARGET
shift
#echo Sources: $@
mkdir -p $TARGET
cp $@ $TARGET
#echo ---------------------