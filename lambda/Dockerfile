FROM public.ecr.aws/lambda/python:3.9
# for further reference, see https://docs.aws.amazon.com/lambda/latest/dg/images-create.html#images-reqs
#checkov:skip=CKV_DOCKER_3::user setup not necessary in lambda context, see link line above

# copy function
COPY . ${LAMBDA_TASK_ROOT}

# install python dependencies
RUN pip3 install --upgrade pip && pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# setup oracle paths
ENV ORACLE_HOME=/opt/oracle
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$ORACLE_HOME/lib

# install oracle client library dependencies
RUN yum update -y \
    && yum install -y libaio unzip \
    && yum clean all \
    && rm -rf /var/cache/yum

# install oracle client library
RUN curl -o instantclient.zip https://download.oracle.com/otn_software/linux/instantclient/213000/instantclient-basic-linux.x64-21.3.0.0.0.zip \
    && unzip instantclient.zip \
    && mkdir -p $ORACLE_HOME \
    && mv instantclient_21_3 $ORACLE_HOME/lib \
    && rm -f instantclient.zip

# see https://docs.aws.amazon.com/lambda/latest/dg/troubleshooting-deployment.html#troubleshooting-deployment-denied
RUN chmod 644 $(find . -type f) && chmod 755 $(find . -type d)

# not required in lambda context
HEALTHCHECK NONE

CMD [ "lambda_handler.handler" ]
