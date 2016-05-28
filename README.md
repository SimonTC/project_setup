Auto setup of new projects
==================

This script is used to setup new python projects.
It performs the following tasks:

* Sets up the following folder structure:
    ```python
    project_name/
        project_name/
             __init__.py
        tests/
            __init__.py
    ```


* Creates a simple conda environment containing pip and python as dependencies.
* Sets up git version control.

The folder structure is from Learn Python The Hard Way.
The environment and git setup is inspired by the following article:
http://stiglerdiet.com/blog/2015/Nov/24/my-python-environment-workflow-with-conda/

