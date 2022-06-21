# PROTEUS Command Line Tools

CLI tools to interact with the plaform. Currently supports.

- Create and update a simulations batch
- Provide files to a dataset
- List a Job status

## Install and setup

1. Clone the project into the desired directory. This repo has submodules so you will need using

```
git clone --recurse-submodules git@github.com:OriGenAI/proteus-cli.git
```


2. Install and setup enviroment

```
virtualenv -p /usr/bin/python3.8 venv
source venv/bin/activate
pip install -r requirements.txt 
# use requirements/dev.txt if you are a developer
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

Credentials can also be type using the proteus line prompt

4. In order to use testing it will be necesary to create the .testenv file with valid proteus credentials, and a proteus-backend host. It will be also neccesary to install the dev requirements.

```
PROTEUS_USERNAME="proteus-username-not-configured"
PROTEUS_PASSWORD="proteus-password-not-configured"
PROTEUS_HOST=http://localhost:5000
```

5. Keeping up-to-date

Remember, to update both the current repo and submodules updated you have to run the following command:

```
git pull --recurse-submodules
```

### Contributors

Please note that to apply correct linting developer properties have to be installed:

```
pip install -r requirements/dev.txt
```

And pre-commit should be installed:

```
pre-commit install
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
proteus simulations create ./home/hesssample --model_uuid=<MODEL_UUID> --batch_name="<NAME-IT>"
```

The system will reply with a --batch_uuid parameter you should use to continue with the upload:

```
proteus simulations create ./home/hesssample --batch_uuid=<BATCH_UUID>
```

use the flag --reupload if you want to force reuploading all the dependencies:

```
proteus simulations create ./home/hesssample --batch_uuid=<BATCH_UUID> --reupload
```

## Dataset upload

### from local filesystem

Once you get an S3 URI that contains the cases groups, and choosen a dataset UUID to upload the source into simply run:

```
proteus datasets upload /home/your-user/your-data 02135a2a-7f73-4f4a-a5ef-843be8a8cf82
```

Process can be run again if failed only missing files will be uploaded

### from Azure

Once you get an Azure URI that contains the dataset input files, and choosen a dataset UUID to upload the source into simply run:

```
proteus datasets upload https://whatever-uri 02135a2a-7f73-4f4a-a5ef-843be8a8cf82
```

Process can be run again if failed only missing files will be uploaded


### from S3 (deprecated)

Once you get an S3 URI that contains the cases groups, and choosen a dataset UUID to upload the source into simply run:

```
proteus datasets uploads s3://whatever-uri/you-selected/cases 02135a2a-7f73-4f4a-a5ef-843be8a8cf82
```

Process can be run again if failed only missing files will be uploaded

## Jobs listing (by entity type)

This proteus requires to specify what kind of jobs you want to list

```
proteus jobs list <samplings|models|simulations>
```

Follow screen instructions to navigate the results

## Job Status

After getting a job UUID (for example from the prevous commnad) simply run:

```
proteus jobs status 114058ca-7342-45ab-99ac-562167cc52e6
```

Follow screen instructions to navigate the results

# Buckets

## Download bucket's contents

As easy as set bucket UUID and a target folder, it will re-create the structure and files won't have it's final filename till the partial download is done. Note that already exitent files will remove previous files when it's download is done.

```
proteus buckets download 17ca1e74-a70c-4598-bfc3-71de915e08cb  ./target_folder  --workers 5 [--ends-with X0001]
```
