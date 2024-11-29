path_file=count_files.txt
count_table=count_table.txt
echo "name,whitelist,count" > $count_table

while IFS= read -r path
do
    name=$( basename $path | cut -d '.' -f 1)
    whitelist=$( basename $path | cut -d '.' -f 3 )
    count=$( cat $path )
    echo "${name},${whitelist},${count}" >> $count_table
done < $path_file
    