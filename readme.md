# CTFd Plugins
This repo includes three plugins for [CTFd](https://github.com/CTFd/CTFd). Each of them can be used independently.

_!!haven't been tested in production yet!!_

---

# challenges_download plugin

### Features

You can download challenges and then upload them to another instance of CTFd.
Serializes chosen challenge and creates ZIP archive of its content and files.
This plugin is useful for backing up challenges.


Requirements:
 - zipfile

![Downloads](images/download_challenges/01_download.jpg)
_Downloads Page_


![Uploads](images/download_challenges/03_uploads.jpg)
_Uploads Page_


![Serialized](images/download_challenges/02_serialized.jpg)
_Example Challenge Serialized_

---

# penalties plugin

### Features

Adds new challenge type. 
This new type has a penalty property 
which decreases the amount of points user gets for solving a challenge.
Penalty can be turned on/off. This plugin can be used for 
challenges that must be solved in the certain amount of time, 
but the penalty has to be activated manually.


![Downloads](images/penalties/01_create.jpg)


![Downloads](images/penalties/02_create_2.jpg)
_Creation Page_


![Downloads](images/penalties/03_penalty.jpg)
_Applied penalty_


---


# group_management plugin


_This plugin was made to make CTFd suitable for education at the university courses._

### Features


Adds a "group" organizational unit. 
A group consists of several teams. Before user can proceed to the challenges he/she has to choose a group.
Admin can set groups active/inactive so that users can or cannot proceed to the challenges page.
Also, admin can create users (students) in a bunch by copy-pasting an Excel table into import section.

_Caution: his plugin overrides setup page and forces Team mode._

![Downloads](images/group_management/01_setup.jpg)
_Setup Page_


![Downloads](images/group_management/02_import.jpg)
_Import Users Page_


![Downloads](images/group_management/04_group_listing.jpg)
_Group listing_


![Downloads](images/group_management/05_create_group.jpg)
_New group creation_


![Downloads](images/group_management/06_group_manage.jpg)
_Group page_


![Downloads](images/group_management/03_group_choice.jpg)
_User has to choose a group_

![Downloads](images/group_management/07_group_forbidden.jpg)
_If group is inactive displays an error message_

