# Attendance Management System (AMS)

### Setup

Firstly let's setup minio as we are using it for storing images(for the current case)

- For windows:
    
    - download minio from https://dl.min.io/server/minio/release/windows-amd64/minio.exe and install it and after installing go to the directory, open the command prompt/terminal and run the following command to start minio
    ```
    minio.exe server C:\minio --console-address :9001
    ```
    it will start the server in your localhost  `http://127.0.0.1:9000` with *minioadmin* as the default id and password 
    
- For MacOS:
    ```bash
    curl --progress-bar -O https://dl.min.io/server/minio/release/darwin-amd64/minio
    chmod +x minio
    MINIO_ROOT_USER=admin MINIO_ROOT_PASSWORD=password ./minio server /mnt/data --console-address ":9001"
    ```
    

After that to set up the project run shell script that will set up everything depending on your operating system

- For mac/linux
    ```bash
    # open shell
    chmod +x app.sh
    ./app.sh
    ```
- For windows
    ```shell  
    # open terminal
    Powershell.exe -File app.ps1
    ```

If something went wrong then you can also do it manually as well by opening that file and running command one by one.

**Note:** Once the script run successfully then it will create a superuser with **email:** *admin@roadcast.com* and **password:** *admin12345* which you can use to create/add employees and managers


### Endpoints

There are 3 types of user:

- Superuser (full control over the app)
- Manager (partial control over the app)
- Staff/Employee (control over the assigned stuff)


**Available Endpoints:**

Majority Endpoints are protected

```bash
Endpoints                            Description                        

/                                   # app index page
admin/                              # admin index page (protected)
staff/                              # staff index page (protected)
admin/signin                        # admin signin page
staff/signin                        # staff signin page
admin/employee                      # view/edit/delete employee/staff dashboard (protected)
admin/employee/add                  # add employee/staff (protected)
admin/employee/timelog/<int:id>     # add employee/staff (protected)(protected)
admin/schedule                      # view/edit/delete schedule dashboard (protected)
admin/schedule/<int:id>             # view/edit/delete assigned schedule for an employee/staff (protected)
admin/schedule/add                  # add schedule (protected)
staff/timelog/add                   # add time log (for manager and employee) (protected)

```

### Architectural Design

The app follows somewhat the MVC architecture.

Components:
- python (flask and some third party extensions for flask) for the app
- minio for as the object storage (images in our current usecase)
- sqlite3 database for storing the information of various components of our app