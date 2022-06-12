# jobtracking
 Deployable Job Tracking Solution

Deployment Instructions (assuming a windows machine:)

Key:
> An instructions
>>> Execute in command line (not powershell)
- Comment


- Install requirements
> Install python 3.10 and git
	-  Make sure Python has been added to the windows PATH variable

- Download source code
>>> cd C:\<your install directory>
>>> git clone https://github.com/alex-benton-cam/jobtracking.git
>>> cd jobtracking

- Install required python packages
>>> python -m pip install --upgrade pip
>>> pip install virtualenvwrapper-win
>>> mkvirtualenv jobtracking env
>>> workon jobtrackingenv
>>> pip install -r requirements.txt
	- This step may take some time

- Setup server
>>> python manage.py makemigrations
>>> python manage.py migrate
>>> python manage.py createsuperuser
	- Complete username and password as prompted
	- You are creating credentials for the overall user of the website

- Find ip address
>>> ipconfig
	- Find your ipv4 address
	- Under Ethernet adpater for an ethernet networked PC 
	- or under Wireless LAN adapter for a wifi-networked pc
	- eg 192.168.0.113

- Run server
>>> python manage.py runserver <your ip>:8001
	- 8001 is a port number, and can be changed if this port is already in use
	- All devices connected to the same network should now be able to view this page,
	- but problems can arise with network firewalls

- Configure the webapp. These steps can be done from any device.
> Connect to the website by typing <your ip>:8001 into the address bar of a browser
> Log in as the superuser 
> Follow the 'Setup Data' link in the sidebar and for each of the four cards shown:
	> Download the example file
	> Make changes to data as necessary
		- Datatable Configurations do not need adjustment by default
	> Reupload the file to configure the site
> Follow the 'Upload Ops' sidebar link
	> Upload some operations, perhaps using the example dat


- Subscribing to manager calls and adding users:
> Navigate to <your ip>:<your port>/admin/shell

- To add a user:
>>> from django.contrib.auth.models import User
>>> user=User.objects.create_user('<your username>', password='<your password>')
>>> user.is_superuser=True
	- Include this line if the user should be able to access the admin site
>>> user.save()
> Run code

- To subscribe to alerts
>>> from core.utils import alert_subscribe
>>> locs = ["T9", "T4"]
	- Use loc_ids to fill this list, see the 'All Locations' page for examples
>>> alert_subscribe('<your username>', locs)
> Run code

