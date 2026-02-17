import os, sys

root = os.getcwd()
post = sys.argv[1]
post_parts = post.split("\\")
folder_images = os.path.join(root, "images");
folder_target = os.path.join(folder_images, post)

if len(post_parts) == 1:
    folder_originals = os.path.join(folder_target, "originals")
else:
    folder_originals = os.path.join(folder_images, post_parts[0], "originals", post_parts[1])

files = [ entry.name for entry in os.scandir(folder_originals) if entry.is_file() ]
files_count = len(files)
counter = 0
for filename in files:
    os.system('cls')
    percent = counter * 100 / files_count
    print("done: " + str(counter) + "/" + str(files_count) + ", " + str(round(percent)) + "%")
    pos = filename.find("-")
    if pos == -1:
        inp = os.path.join(folder_originals, filename)
        filename = os.path.splitext(filename.lower())[0] + ".jpg";
        outp = os.path.join(folder_target, filename)
        cmd = "scripts\process_image.bat \"" + inp + "\" \"" + outp + "\""
        os.system(cmd)
    else:
        name = filename[0:pos]
        part = int(filename[pos + 1:filename.rfind(".")])
        if part == 1:
            tmp1, ext1 = os.path.splitext(filename)
            inp1 = os.path.join(folder_originals, name + "-1" + ext1)

            tmp2, ext2 = os.path.splitext(files[counter + 1])
            inp2 = os.path.join(folder_originals, name + "-2" + ext2)

            outp = os.path.join(folder_target, name + ".jpg")
            cmd = "scripts\process_image.bat \"" + inp1 + "\" \"" + inp2 + "\" \"" + outp + "\""
            os.system(cmd)
    counter += 1

os.system('cls')
percent = counter * 100 / files_count
print("done: " + str(counter) + "/" + str(files_count) + ", " + str(round(percent)) + "%")
