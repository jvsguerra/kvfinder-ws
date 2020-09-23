# Valuable informations for developers

This manual aims to aid developers with some relevant information about KVFinderWebTools operation. 

## Threads

The KVFinder Web Tools has two threads:

- **Graphical User Interface (GUI)** thread: `class PyMOLKVFinderWebTools(QMainWindow)` that handles the interface objects, slots, signals and functions;

- **Worker** thread: `class Worker` that checks constantly the jobs sent to KVFinder-web server (https://server-url) and automatically downloads them when completed.


## Possible QNetworkReply.error():

Responses from KVFinder-web server when `QNetwork.AccessManager()` sents a `.get()` or `.post()` request:

- **0**: No Error

- **1**: Connection Refused Error

- **203**: The remote content was not found at the server
