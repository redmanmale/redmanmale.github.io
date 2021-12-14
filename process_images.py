import os, sys

root = os.getcwd()
post = sys.argv[1]
folder_target = os.path.join(root, "images", post)
folder_originals = os.path.join(folder_target, "originals")

for filename in os.listdir(folder_originals):
    print("Processing " + filename)
    pos = filename.find("-")
    if pos == -1:
        inp = os.path.join(folder_originals, filename)
        outp = os.path.join(folder_target, filename.lower())
        cmd = "c2post \"" + inp + "\" \"" + outp + "\""
        os.system(cmd)
    else:
        name = filename[0:pos]
        part = int(filename[pos + 1:filename.rfind(".")])
        if part == 1:
            inp1 = os.path.join(folder_originals, name + "-1.jpg")
            inp2 = os.path.join(folder_originals, name + "-2.jpg")
            outp = os.path.join(folder_target, name + ".jpg")
            cmd = "c2post \"" + inp1 + "\" \"" + inp2 + "\" \"" + outp + "\""
            os.system(cmd)
