webdisplay
==========

Small remote display of images. The server is implemented in Python and the client is a web page. 
The server can be used to display images from a Python program on a web page. 
Its main use is for debugging and monitoring purposes, but it can also be used for other applications.
The same philosophy as X11 but for the web.

Installation
------------

.. code-block:: bash

    pip install webdisplay

Server Usage
------------

.. code-block:: bash

    webdisplay-server --port 8765  # default port is 8765

This will start a server on port 8765 and open a web browser connected to this server. You can change the port if needed.
There is also a `--no-browser` option to prevent the browser from opening automatically. 
This is useful if you want to send images from a remote machine to your local machine.


The client produce a figure, use the webdisplay client to send it to the server then the server will display it on the web page. 
You can send multiple figures and they will be displayed as a list of pictures in the web page.

Client Usage
------------

.. code-block:: python

    import webdisplay
    import matplotlib.pyplot as plt

    # should be called only once in the program, before any other webdisplay function is called
    webdisplay.connect("ws://localhost:8765/send")  # most likely the default address, but you can change it if needed

    fig, ax = plt.subplots()
    ax.plot([1, 4, 2, 8, 5])
    webdisplay.show_figure(fig)

