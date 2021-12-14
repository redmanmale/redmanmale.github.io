@echo off
setlocal enableextensions

rem get number of args
set args=0
for %%x in (%*) do set /A args+=1

if %args% equ 2 (
    goto one_photo
)

rem get width and height of the first one
set cmd="magick identify -ping -format "%%w" %1"
for /f "tokens=*" %%g in ('%cmd%') do (set width=%%g)

set cmd="magick identify -ping -format "%%h" %1"
for /f "tokens=*" %%g in ('%cmd%') do (set height=%%g)

set real_width=3024
set real_height=4032

if %width% equ %real_width% (
    if %height% equ %real_height% (
        goto my_two_photos
    )
)

if %width% equ %real_height% (
    if %height% equ %real_width% (
        rem if photos from phone they must be rotated
        set extra=-rotate 90
        goto my_two_photos
    )
)

goto any_two_photos

:one_photo
rem resize any photo to 1000px
magick convert %1 -resize 1000 %2

goto eof

:my_two_photos
rem for a photos 3024x4032

rem combine 2 photos to 1 with the 50px horizontal space
magick montage %extra% %1 %2 -tile x1 -geometry +50+0 "%temp%\temp.jpg"

rem resize and remove 50px outer space
magick convert "%temp%\temp.jpg" -shave 50x0 -resize 1000 %3

goto cleanup

:any_two_photos
rem for any photos to 492 x 2 + space 16 between = 1000

rem combine 2 photos to 1, resize and add 8px horizontal space
magick montage %1 %2 -tile x1 -geometry 492x+8+0 "%temp%\temp.jpg"

rem remove 8px outer space
magick convert "%temp%\temp.jpg" -shave 8x0 %3

goto cleanup

:cleanup
timeout /t 2 /nobreak > nul
del "%temp%\temp.jpg"

goto eof

:eof
