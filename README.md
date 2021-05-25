# {{your-project-name}} based on proteus-runner

Proposed structure for a worker. Put here your doc description

## First steps

1. Create your project

2. Link this project as a `template` remote and pull `dev` branch

```
git remote add template git@github.com:OriGenAI/proteus-runner.git 
git pull template dev --allow-unrelated-stories
```

Now on to update you only have to do

```
git pull template dev
```


3. Setting the project terms

Edit `project.py` to fill in the addecuate project terms


4. All done

Once created you can remove this section on the doc


## Initial setup for {{your-project-name}}


1. Install and setup enviroment

```
virtualenv -p3.8 venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements/dev.txt
pip install -e .
pre-commit install
```
2. Optionally you can create basic dockerfiles and a update script
```
python setup.py docker
```


## Running de project

first time:

1. Copy and customize a `env.sh.template` to `env.sh`

First and succesive times:

2. Import it using `source env.sh`
3. Run it: `run`
