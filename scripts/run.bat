del ..\tag /q
del ..\_site /q
python tag_generator.py
jekyll serve --host=0.0.0.0 -s .. -d ..\_site
