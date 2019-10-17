import logging
import json
import os
import datetime

from google.oauth2 import service_account
from google.cloud import bigtable
from google.cloud import monitoring_v3
from google.cloud.monitoring_v3 import query

def slack_notify(new_node_count,cluster_cpu,scale_up, cluster_payload, current_node_count):
    import requests

    cluster_cpu_percentage = '{0:.2%}'.format(cluster_cpu)
    if scale_up == True:
        scale = ":small_red_triangle:"
    else:
        scale = ":small_red_triangle_down:"

    webhook_url = 'https://hooks.slack.com/services/<<<< SLACK WEBHOOK TOKEN HERE >>>>>'
    message = '[{"type":"section","text":{"type":"mrkdwn","text":"%s *Instance:* %s :: *CPU:* %s :: *Nodes*: %s -> %s"},"accessory":{"type":"button","text":{"type":"plain_text","text":"Settings","emoji":true},"url":"https://github.com/bdgscotland/bigtable-autoscaler-function/new/master"}},{"type":"divider"}]' % (scale, cluster_payload['bigtable'][0]['name'], cluster_cpu_percentage, current_node_count, new_node_count)

    slack_data = json.dumps({'blocks': message})
    response = requests.post(webhook_url, data=slack_data, headers={'Content-Type': 'application/json'})

    if response.status_code != 200:
        raise ValueError(
          'Request to slack returned an error %s, the response is:\n%s'
          % (response.status_code, response.text)
        )

def get_cpu(cluster_payload):
    client = monitoring_v3.MetricServiceClient()
        #THIS NEEDS A FILTER!!!!
    cpu_query = query.Query(client,
                            project=gcproject,
                            metric_type='bigtable.googleapis.com/'
                                        'cluster/cpu_load',
                            minutes=5).select_resources(cluster=cluster_payload['bigtable'][0]['cluster'])
    time_series = list(cpu_query)
    recent_time_series = time_series[0]
    return recent_time_series.points[0].value.double_value


def bt_scale(cluster_payload, scale_up, cluster_cpu):
    SIZE_UP_CHANGE_STEP = 2
    SIZE_DOWN_CHANGE_STEP = 1

    bigtable_client = bigtable.Client(admin=True,project=gcproject)
    instance = bigtable_client.instance(cluster_payload['bigtable'][0]['name'])
    instance.reload()

    cluster_object = instance.cluster(cluster_payload['bigtable'][0]['cluster'])
    cluster_object.reload()

    current_node_count = cluster_object.serve_nodes

    if scale_up:
        if current_node_count < cluster_payload['bigtable'][0]['nodes'][0]['max']:
            new_node_count = min(current_node_count + SIZE_UP_CHANGE_STEP, cluster_payload['bigtable'][0]['nodes'][0]['max'])
            cluster_object.serve_nodes = new_node_count
            cluster_object.update()
            logging.info('{} :: Scaled up from {} to {} nodes.'.format(datetime.datetime.now(), current_node_count, new_node_count))
            slack_notify(new_node_count, cluster_cpu, True, cluster_payload, current_node_count)
        else:
            logging.warning('{} :: Currently at a maximum node count of {}. Consider increasing the project quota if this value cannot be set higher.'.format(datetime.datetime.now(), cluster_payload['bigtable'][0]['nodes'][0]['max']))

    else:
        if current_node_count > cluster_payload['bigtable'][0]['nodes'][0]['min']:
            new_node_count = max(current_node_count - SIZE_DOWN_CHANGE_STEP, cluster_payload['bigtable'][0]['nodes'][0]['min'])
            cluster_object.serve_nodes = new_node_count
            cluster_object.update()
            logging.info('{} :: Scaled down from {} to {} nodes.'.format(datetime.datetime.now(), current_node_count, new_node_count))
            slack_notify(new_node_count, cluster_cpu, False, cluster_payload, current_node_count)
        else:
            if cluster_payload['bigtable'][0]['nodes'][0]['min'] == 3:
                logging.info('{} :: Currently at minimum node count of {}. This is as low as this value can go.'.format(datetime.datetime.now(), current_node_count))

            else:
                logging.warning('{} :: Currently at minimum node count of {}. Consider decreasing the min_node_count value.'.format(datetime.datetime.now(), current_node_count))



def scaler(cluster_payload):
    global gcproject
    gcproject = os.environ['GCLOUD_PROJECT']
    logging.info('{} :: Google Project {} : Triggered Cluster {}'.format(datetime.datetime.now(), gcproject,cluster_payload['bigtable'][0]['name']))
    cluster_cpu = get_cpu(cluster_payload)

    if cluster_cpu > cluster_payload['bigtable'][0]['cpu'][0]['high']:
        logging.info('{} :: Detected cpu of {}, higher than the configured threshold of {}. Attempting to scale up.'.format(datetime.datetime.now(), cluster_cpu, cluster_payload['bigtable'][0]['cpu'][0]['high']))
        #print('I would have scaled up here')
        bt_scale(cluster_payload, True, cluster_cpu)
    elif cluster_cpu < cluster_payload['bigtable'][0]['cpu'][0]['low']:
        logging.info('{} :: Detected cpu of {}, lower than the configured threshold of {}. Attempting to scale down.'.format(datetime.datetime.now(), cluster_cpu, cluster_payload['bigtable'][0]['cpu'][0]['low']))
        #print('I would have scaled down here')
        bt_scale(cluster_payload, False, cluster_cpu)


def process_payload(event, context):
    import base64

    print("""Bigtable Autoscaler was triggered by messageId {} published at {}
    """.format(context.event_id, context.timestamp))

    if 'data' in event:
        pubsub_payload = base64.b64decode(event['data']).decode('utf-8')
        pubsub_payload = pubsub_payload.replace('\n', ' ')
        json_payload = json.loads(pubsub_payload)
        print('{}'.format(json_payload))
        #print(json_payload['bigtable'][0]['name'])

        return json_payload




def main(event, context):
    cluster_payload = process_payload(event, context)
    scaler(cluster_payload)
