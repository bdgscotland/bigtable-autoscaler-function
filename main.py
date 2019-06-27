import argparse
import time
import datetime
import os
import logging
import json
import sys
import string
import yaml

from requests import get

from google.oauth2 import service_account
from google.cloud import bigtable
from google.cloud import monitoring_v3
from google.cloud.monitoring_v3 import query

gcproject = None

def _check_token_auth(auth_token_yaml,auth_token_webhook):
    return auth_token_yaml == auth_token_webhook

def _load_data(request):
    #load YAML from file
    with open("bts_data.yml", 'r') as stream:
        try:
            yaml_data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    #load JSON from inbound POST
    request_json = request.get_json(silent=True)
    auth_token = request.args.get('auth_token','no_token')
    
    logging.info('Invoked from : %s %s %s\n', request.remote_addr, request.method, request.scheme)
    logging.info("{} :: JSON payload from Alert: {}".format(datetime.datetime.now(),request_json))
    logging.info("{} :: YAML payload from File: {}".format(datetime.datetime.now(),yaml_data))
    
    bt_cluster = request_json['incident']['resource']['labels']['cluster']
    bt_instance = request_json['incident']['resource']['labels']['instance']

    cluster = {
            "auth_token_yaml": yaml_data['auth_token'],
        	"auth_token_webhook": auth_token,
            "bt_cluster": bt_cluster,
            "bt_instance": bt_instance,
            "min_node_count": yaml_data[bt_instance]['min_node_count'],
            "max_node_count": yaml_data[bt_instance]['max_node_count'] }

    return cluster


def client_handler(request):
    cluster = _load_data(request)
    
    if not cluster['auth_token_webhook'] or not _check_token_auth(cluster['auth_token_yaml'], cluster['auth_token_webhook']):
        return ('403 Hoots min - Yir barred', 403)
    else:
        logging.info("202 Token Accepted - Welcome to BTS")
        scaler(cluster)
        return ('OK', 202)


###

def get_cpu(cluster):
    client = monitoring_v3.MetricServiceClient()
	#THIS NEEDS A FILTER!!!!
    cpu_query = query.Query(client,
                            project=gcproject,
                            metric_type='bigtable.googleapis.com/'
                                        'cluster/cpu_load',
                            minutes=5).select_resources(cluster=cluster['bt_cluster'])
    time_series = list(cpu_query)
    recent_time_series = time_series[0]
    return recent_time_series.points[0].value.double_value

def bt_scale(cluster, scale_up):
    SIZE_UP_CHANGE_STEP = 2
    SIZE_DOWN_CHANGE_STEP = 1
    
    bigtable_client = bigtable.Client(admin=True,project=gcproject)
    instance = bigtable_client.instance(cluster['bt_instance'])
    instance.reload()

    cluster_object = instance.cluster(cluster['bt_cluster'])
    cluster_object.reload()
    
    current_node_count = cluster_object.serve_nodes

    if scale_up:
        if current_node_count < cluster['max_node_count']:
            new_node_count = min(current_node_count + SIZE_UP_CHANGE_STEP, cluster['max_node_count'])
            cluster_object.serve_nodes = new_node_count
            cluster_object.update()
            logging.info('{} :: Scaled up from {} to {} nodes.'.format(datetime.datetime.now(), current_node_count, new_node_count))
        else:
            logging.warning('{} :: Currently at a maximum node count of {}. Consider increasing the project quota if this value cannot be set higher.'.format(datetime.datetime.now(), cluster['max_node_count']))

    else:
        if current_node_count > cluster['min_node_count']:
            new_node_count = max(current_node_count - SIZE_DOWN_CHANGE_STEP, cluster['min_node_count'])
            cluster_object.serve_nodes = new_node_count
            cluster_object.update()
            logging.info('{} :: Scaled down from {} to {} nodes.'.format(datetime.datetime.now(), current_node_count, new_node_count))

        else:
            if cluster['min_node_count'] == 3:
                logging.info('{} :: Currently at minimum node count of {}. This is as low as this value can go.'.format(datetime.datetime.now(), current_node_count))

            else:
                logging.warning('{} :: Currently at minimum node count of {}. Consider decreasing the min_node_count value.'.format(datetime.datetime.now(), current_node_count))


def scaler(cluster):
    global gcproject
    gcproject = os.environ['GCLOUD_PROJECT']
    
    logging.info('{} Google Project {}'.format(datetime.datetime.now(), gcproject))
    high_cpu_threshold = 0.8
    low_cpu_threshold = 0.5
    
    cluster_cpu = get_cpu(cluster)
    
    if cluster_cpu > high_cpu_threshold:
        logging.info('{} :: Detected cpu of {}, higher than the configured threshold of {}. Attempting to scale up.'.format(datetime.datetime.now(), cluster_cpu, high_cpu_threshold))
        #print('I would have scaled up here')
        bt_scale(cluster, True)
    elif cluster_cpu < low_cpu_threshold:
        logging.info('{} :: Detected cpu of {}, lower than the configured threshold of {}. Attempting to scale down.'.format(datetime.datetime.now(), cluster_cpu, low_cpu_threshold))
        #print('I would have scaled down here')
        bt_scale(cluster, False)



def main(request):
    return client_handler(request)

