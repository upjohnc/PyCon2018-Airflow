import airflow
from airflow.operators.python_operator import PythonOperator
from airflow.models import DAG
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults

import requests

import time
import zipfile
import os

args = {
    'owner': 'pycon',
    'start_date': airflow.utils.dates.days_ago(2)
}

dag = DAG(
    dag_id='solution5', default_args=args,
    schedule_interval=None)


# executables
def download_names():
    location = "https://www.ssa.gov/oact/babynames/names.zip"

    local_filename = "/tmp/work/names.zip"

    print("Starting download...")
    r = requests.get(location, stream=True)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

    print("Finished downloading names!")
    return local_filename


def unzip_names():
    input_file = "/tmp/work/names.zip"
    names_directory = "/tmp/work/"

    print("Starting unzipping...")
    zip_ref = zipfile.ZipFile(input_file, 'r')
    zip_ref.extractall(names_directory)
    zip_ref.close()
    print("Unzip finished!")

class FindCommonOperator(BaseOperator):
  @apply_defaults
  def __init__(self, *args,
        names_directory='/tmp/work/', **kwargs):
      self.names_directory = names_directory
      super(FindCommonOperator, self).__init__(
            *args, **kwargs)
      
  def execute(self, context):
      files = os.listdir(self.names_directory)
      names = {}

      print("Finding common name...")
      for f in files:
          if f.endswith('.txt'):
              with open(os.path.join(self.names_directory, f)) \
                        as current:
                  for row in current:
                      name, gender, count = row.split(",")
                      if name in names:
                          names[name] += int(count)
                      else:
                          names[name] = int(count)

      common_name = sorted(
        names, key=names.get, reverse=True)[0]
      print("Common name is {}".format(common_name))

      return common_name


# tasks
download_task = PythonOperator(
    task_id='download',
    python_callable=download_names,
    dag=dag)

unzip_task = PythonOperator(
    task_id='unzip',
    python_callable=unzip_names,
    dag=dag)

find_common_task = FindCommonOperator(
    task_id='find_common',
    dag=dag)


# dependencies
unzip_task.set_upstream(download_task)
find_common_task.set_upstream(unzip_task)
