Installation
========================================

Install **littletree** using `pip <https://pip.pypa.io/en/stable/getting-started/>`_:

    $ pip install --upgrade littletree

If you want to enable all export functions, install with optional dependencies:

    $ pip install --upgrade littletree[export]

External dependencies
---------------------

For the function ``to_image`` and related functions (e.g. ``to_pillow``) to work, the following command-line tools should be available on your system ``PATH``:

* `Graphviz <https://graphviz.org/download/>`_
* `Mermaid CLI <https://github.com/mermaid-js/mermaid-cli>`_ (required only if using ``to_image(..., how="mermaid")``)

Alternatively, you can pass an explicit program path, for example::

    tree.to_image(program_path="C:/path/to/dot.exe")
