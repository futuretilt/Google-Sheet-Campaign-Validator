FROM public.ecr.aws/lambda/python:3.11

# Copy requirements file
COPY requirements.txt ${LAMBDA_TASK_ROOT}/

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy function code
COPY sheet_columns.py ${LAMBDA_TASK_ROOT}/

# Set the CMD to your handler
CMD ["sheet_columns.lambda_handler"]