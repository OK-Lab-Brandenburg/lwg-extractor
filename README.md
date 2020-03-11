# Lausitzer Wasser GmbH (LWG) data extractor

This python script extract data form LWG website about water values. Downloads all provided PDFs and extract specific values from data tables inside PDF documents.


## Development

Dependencies:

 * OpenCV
 * Ghostscript
 * Python3
 * Python3-tk

Python script has some dependencies, installation with commands below.

```shell
# create python virutal environment
$ python -m venv venv
# activate venv
$ source venv/bin/activate
```

## Execute

```shell
$ python lwg-extractor.py <output name json file>
```

