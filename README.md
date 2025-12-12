# XTC generator

for some reason or another I just couldn't get the website generator or the other python generator to run. Hencce the creation of this. It uses calibre to convert the epubs to pdf in a certain size first then converts that pdf into an xtc file format by splitting the images out first then creating the xtc file based on the folder of images.

---

# Disclaimer

`creatextc.py` is fully ai generated based on the spec which is ai generated. but so far everything works :D\
`main.py` is mostly ai generated

---

# Setup

Packages needed are inside requirements.txt and you can install it via

```bash
pip install -r requirements.txt
```


# How to Use

Steps:

- Convert your books to pdf format using calibre\
    make sure the size of the page is `480x800 points`
This can be set under
  ```
  PDF output > Custom Size: "480x800" then change the units to points
  ```
- Export the books into the folder `books` 
    ```
    select all books > right click books > save to disk > export single format to disk
    ```
    does not matter where the pdf folder is in the `books` folder as the code will search all subfolders
- Run `main.py` with python3
    ```bash
    python3 main.py
    ```

`main.py` crawls through the books directory for pdf to format

# Other functionality

you can run the following to split a pdf in 480x800 into images in 1 bit format to see how it looks like

```bash
python3 convertpdf.py [filename]
```

and you can create a xtc file based on the folder `output_images` with images in 1 bit the following command:

```bash
python3 creatextc.py [output file name]
```

