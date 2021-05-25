#/bin/sh
set -e  # Will cause error to abot the process
. ./customers/check.sh 

export IMAGE_NAME=proteus-UNKNOWN-runner
export IMAGE_TAG=0.2b0

check_image_settings

export FULL_IMAGE_PATH=$IMAGE_REGISTRY/$IMAGE_PROJECT/$IMAGE_NAME:$IMAGE_TAG

export BASIS_IMAGE_TAG=0.1
export BASIS_IMAGE_NAME=proteus-UNKNOWN-runner-requirements


export FULL_BASIS_IMAGE_PATH=$IMAGE_REGISTRY/$IMAGE_PROJECT/$BASIS_IMAGE_NAME:$BASIS_IMAGE_TAG
if ! docker image inspect $FULL_BASIS_IMAGE_PATH >/dev/null 2>&1 
then
    echo "Building requirements image"
    docker build -t $FULL_BASIS_IMAGE_PATH  -f - . < Dockerfile-basis
    docker push $FULL_BASIS_IMAGE_PATH
else
    echo "Requirementes image already present."
fi

echo "protecting private code"
CURRENT_IMAGE=$FULL_IMAGE_PATH python command.py protect \
    --path private --target private-protected
echo "Building image and publishing..."
docker build -t $FULL_IMAGE_PATH . \
    --build-arg BASIS_IMAGE=$FULL_BASIS_IMAGE_PATH \
    --build-arg CURRENT_IMAGE=$FULL_IMAGE_PATH \
    --build-arg PROTECTED_PRIVATE_PATH=./private-protected
docker push $FULL_IMAGE_PATH
