
# PhotoTools (DigiKam)

This is a suite of tools that can help with managing photos in combination with DigiKam. These tools were created with the help of artificial intelligence.



## Documentation

This suite has 3 tools.

1. Backupscript 
This tool backups your digikam database and the pictures it contains. This tool needs to be edited and changed according to the
* SSD_MODEL, 
* SSD_DEVICE
* SSD_MOUNT_POINT
* SOURCE DIRECTORIES
By changing these variables and running the script you will be able to backup everything to the ssd. Note that the auto mounting for some reason does not work, it will dismount the ssd by itself.

2. RAWtoJPGSync
This tool will sync the rating (stars) you gave your RAW files and sync them to the jpg files in the other directory (whenever you export to 2 seperate directories in DigiKam). It can be used by doing the following command:

`./syncXMPRatingtoJPG.sh -p [Path To Folder inside Album that contains JPG and RAW folder.] `

Not that for this tool it is needed to change your DigiKam settings:

* Top Right -> Settings -> Configure Digikam -> Metadata -> Sidecars -> Enable read & write. 

3. Stats
This tool simply shows you what pictures you made but is still a W.I.P. change accordingly to your things, idk i hope you can read python.