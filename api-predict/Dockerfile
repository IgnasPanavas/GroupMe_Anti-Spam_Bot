FROM public.ecr.aws/lambda/python:3.9

# Install system dependencies for scikit-learn
RUN yum update -y && \
    yum install -y gcc gcc-c++ make && \
    yum clean all

# Copy requirements and install Python dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install --no-cache-dir -r requirements.txt

# Copy function code and model files
COPY lambda_function.py ${LAMBDA_TASK_ROOT}
COPY data/ ${LAMBDA_TASK_ROOT}/data/

# Set the CMD to your handler
CMD ["lambda_function.lambda_handler"]
