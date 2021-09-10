# PROTEUS Command Line Tools

CLI tools to interact with the plaform. Currently supports.

* Create and update a simulations batch
* Provide files to a dataset
* List a Job status


## Install and setup

1. Clone the project into the desired directory

2. Install and setup enviroment

```
virtualenv -p3.8 venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

3. create an environtment var shell script to handle configurations
```
#!/bin/sh
export AWS_SERVER_PUBLIC_KEY=XXXXXXXXXXXXXX
export AWS_SERVER_SECRET_KEY=YYYYYYYYYYYYYYYYY
export OIDC_HOST=https://auth.dev.origen.ai
export REALM="origen"
export PROTEUS_HOST=https://proteus-test.dev.origen.ai

#optional export PROTEUS_USERNAME="your_account@origen.ai"
#optional export PROTEUS_PASSWORD="secret-password"
```

## Before using 

On next times prior to use the CLI simpy use this command
```
source venv/bin/activate
source secrets.sh
```

## Simulations 

### Create a new simulation

Simply choose a folder which contains a set of DATA files and their dependencies.
```
command simulations /home/hesssample --model_uuid=<MODEL_UUID> --batch_name="<NAME-IT>"
```
The system will reply with a --batch_uuid parameter you should use to continue with the upload:

```
command simulations /home/hesssample --batch_uuid=<BATCH_UUID>
```

## Dataset upload

### from local filesystem

Once you get an S3 URI that contains the cases groups, and choosen a dataset UUID to upload the source into simply run:

```
command upload /home/your-user/your-data 02135a2a-7f73-4f4a-a5ef-843be8a8cf82
``` 

Process can be run again if failed only missing files will be uploaded


### from S3

Once you get an S3 URI that contains the cases groups, and choosen a dataset UUID to upload the source into simply run:

```
command upload s3://whatever-uri/you-selected/cases 02135a2a-7f73-4f4a-a5ef-843be8a8cf82
``` 

Process can be run again if failed only missing files will be uploaded

## Jobs listing (by entity type)

This command requires to specify what kind of jobs you want to list

```
command listjobs <samplings|models|simulations>
```

Follow screen instructions to navigate the results

## Job Status

After getting a job UUID (for example from the prevous commnad) simply run:

```
command jobstatus 114058ca-7342-45ab-99ac-562167cc52e6
```

Follow screen instructions to navigate the results
