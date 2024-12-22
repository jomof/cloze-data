
#echo ---------------------
export TARGET=$1
rm -rf $TARGET
#echo Target: $TARGET
shift
#echo Sources: $@
mkdir -p $TARGET
cp $@ $TARGET
#echo ---------------------