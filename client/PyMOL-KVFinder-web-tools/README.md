# Guide for developers

This guide aims to aid developers with some relevant information about PyMOL KVFinder-web Tools operation. 

## Classes

### PyMOL KVFinder Web Tools

### Worker

### Form

### Job

## Threads

The KVFinder Web Tools has two threads:

- **Graphical User Interface (GUI)** thread: `class PyMOLKVFinderWebTools(QMainWindow)` that handles the interface objects, slots, signals and functions;

- **Worker** thread: `class Worker(QThread)` that checks constantly the jobs sent to KVFinder-web server (https://server-url) and automatically downloads them when completed.

### GUI thread

### Worker thread


## Possible QNetworkReply.error():

Responses from KVFinder-web server when `QNetwork.AccessManager()` sents a `.get()` or `.post()` request:

- **0**: No Error

- **1**: Connection Refused Error

- **203**: The remote content was not found at the server
