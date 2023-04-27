# **hw05_final**
### **Description**
Social network of bloggers.

Community for publications. A blog with the possibility of publishing posts, subscribing to groups and authors, as well as commenting on posts.

### **Stack**
![python version](https://img.shields.io/badge/Python-3.9-green)
![django version](https://img.shields.io/badge/Django-2.2-green)
![pillow version](https://img.shields.io/badge/Pillow-8.3-green)
![pytest version](https://img.shields.io/badge/pytest-6.2-green)
![requests version](https://img.shields.io/badge/requests-2.26-green)
![sorl-thumbnail version](https://img.shields.io/badge/thumbnail-12.7-green)

### **Launching a project in dev mode**
The instruction is focused on the windows operating system and the git bash utility.<br/>
For other tools, use analogs of commands for your environment.

1. Clone the repository and go to it in the command line:

```
git clone git@github.com:dtankhaev/hw05_final.git
```

```
cd hw05_final
```

2. Install and activate the virtual environment
``
python -m venv venv
``` 
```
source venv/Scripts/activate
```

3. Install the dependencies from the file requirements.txt
``
pip install -r requirements.txt
```

4. In the file folder manage.py perform migrations:
``
python manage.py migrate
```

5. In the file folder manage.py start the server by running the command:
``
python manage.py runserver
``

### *What users can do*:

**Logged in** Users can:
1. View, publish, delete and edit their publications;
2. View information about communities;
3. View and post comments on your own behalf to the publications of other users * (including yourself)*, delete and edit **your** comments;
4. Subscribe to other users and view **your** subscriptions.<br/>
***Note***: Access to all write, update and delete operations is available only after authentication and receipt of the token.

**Anonymous :alien:** users can:
1. View publications;
2. View information about communities;
3. View comments;


### **Author**
[Danzan Tankhaev](https://github.com/dtankhaev )
