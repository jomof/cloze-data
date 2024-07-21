
#!/bin/bash

# Define the file name
file="JMdict_e_examp.gz"

if [ ! -e "$file" ]; then
    curl -O http://example.com/path/to/JMdict_e_examp.gz
fi


cp $file $BUILD_WORKING_DIRECTORY/$file

