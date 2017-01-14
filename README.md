#Cavalcade

Python wrapper for [C.A.V.A.](https://github.com/karlstav/cava) utility with his own drawing window, gui settings and basic audio player functions.

Screenshot
![](http://i.imgur.com/D6I21lL.png)

####Dependencies

######Base
* C.A.V.A.
* GTK+ >=3.18
* Python >=3.5
* Cairo

And all necessary python bindings e.g. python3-gi, python3-cairo.

######Optional
* GStreamer >=1.0
* Python Pillow

####Installation
This is pure python package, so you can try it without install:
```bash
$ git clone https://github.com/worron/cavalcade.git ~/cavalcade
$ python3 ~/cavalcade/cavalcade/run.py
```
For proper install launch `setup.py` script.

####Usage
To use spectrum audio visualizer launch cavalcade without any arguments.  
To use cavalcade as player launch it with `--play` option and list of files:
```bash
$ cavalcade --play audio.mp3
```
Use help command to get list of all available arguments:
```bash
$ cavalcade --help
```