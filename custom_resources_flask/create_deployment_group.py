import json
import logging
import urllib.request

import boto3

SUCCESS = "SUCCESS"
FAILED = "FAILED"

# Configure logging
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

client = boto3.client('codedeploy')


# Lambda Handler
def handler(event, context):
    LOGGER.info("Received event: " + json.dumps(event, indent=2))

    request_type = event['RequestType']

    if request_type == 'Create':
        create_deployment_group(event, context)
    elif request_type == 'Update':
        update_deployment_group(event, context)
    elif request_type == 'Delete':
        delete_deployment_group(event, context)


def create_deployment_group(event, context):
    data = {}
    status = FAILED
    deployment_group_name_ = None
    try:
        application_name_ = event['ResourceProperties']['ApplicationName']
        deployment_group_name_ = event['ResourceProperties']['DeploymentGroupName']
        deployment_config_name_ = event['ResourceProperties']['DeploymentConfigName']
        service_role_arn_ = event['ResourceProperties']['ServiceRoleArn']
        app_target_group_ = event['ResourceProperties']['AppTargetGroup']
        app_listener_arn_ = event['ResourceProperties']['AppListenerArn']
        cluster_name_ = event['ResourceProperties']['EcsClusterName']
        service_name_ = event['ResourceProperties']['EcsServiceName']


        client.create_deployment_group(
            applicationName=application_name_,
            deploymentGroupName=deployment_group_name_,
            deploymentConfigName=deployment_config_name_,
            serviceRoleArn=service_role_arn_,
            deploymentStyle={
                'deploymentType': 'IN_PLACE',
                'deploymentOption': 'WITHOUT_TRAFFIC_CONTROL'
            },
            ecsServices=[
                {
                    'serviceName': service_name_,
                    'clusterName': cluster_name_
                },
            ],
            loadBalancerInfo={
                'targetGroupInfoList': [ 
                    { 
                        'name': app_target_group_
                    }
                ]
            }
        )
        data = {
            "event": "Resource created",
            "deploymentGroupName": deployment_group_name_
        }
        status = SUCCESS
    except BaseException as e:
        raise e
    finally:
        send(event=event,
             context=context,
             physical_resource_id=deployment_group_name_,
             response_status=status,
             response_data=data)


def update_deployment_group(event, context):
    data = {}
    status = FAILED
    new_deployment_group_name_ = None
    try:
        application_name_ = event['ResourceProperties']['ApplicationName']
        deployment_group_name_ = event['ResourceProperties']['DeploymentGroupName']
        deployment_config_name_ = event['ResourceProperties']['DeploymentConfigName']
        service_role_arn_ = event['ResourceProperties']['ServiceRoleArn']
        app_target_group_ = event['ResourceProperties']['BlueTargetGroup']
        app_listener_arn_ = event['ResourceProperties']['ProdListenerArn']
        cluster_name_ = event['ResourceProperties']['EcsClusterName']
        service_name_ = event['ResourceProperties']['EcsServiceName']

        client.update_deployment_group(
            applicationName=application_name_,
            deploymentGroupName=deployment_group_name_,
            deploymentConfigName=deployment_config_name_,
            serviceRoleArn=service_role_arn_,
            deploymentStyle={
                'deploymentType': 'IN_PLACE',
                'deploymentOption': 'WITHOUT_TRAFFIC_CONTROL'
            },
            ecsServices=[
                {
                    'serviceName': service_name_,
                    'clusterName': cluster_name_
                },
            ],
            loadBalancerInfo={
                'targetGroupInfoList': [ 
                    { 
                        'name': app_target_group_
                    }
                ]
            }
        )
        data = {
            "event": "Resource updated",
            "deploymentGroupName": deployment_group_name_
        }
        status = SUCCESS
    except BaseException as e:
        raise e
    finally:
        send(event=event,
             context=context,
             physical_resource_id=deployment_group_name_,
             response_status=status,
             response_data=data)


def delete_deployment_group(event, context):
    data = {}
    status = FAILED
    try:
        application_name_ = event['ResourceProperties']['ApplicationName']
        deployment_group_name_ = event['ResourceProperties']['DeploymentGroupName']

        client.delete_deployment_group(
            applicationName=application_name_,
            deploymentGroupName=deployment_group_name_
        )
        status = SUCCESS

        data = {
            "event": "Resource deleted",
            "deploymentGroupName": deployment_group_name_
        }
    except BaseException as e:
        raise e
    finally:
        send(event=event,
             context=context,
             physical_resource_id=deployment_group_name_,
             response_status=status,
             response_data=data)


def send(event, context, response_status, response_data, physical_resource_id=None, no_echo=False):
    response_url = event['ResponseURL']

    LOGGER.info(response_url)

    response_body = {
        'Status': response_status,
        'Reason': 'See the details in CloudWatch Log Stream: ' + context.log_stream_name,
        'PhysicalResourceId': physical_resource_id or context.log_stream_name, 'StackId': event['StackId'],
        'RequestId': event['RequestId'], 'LogicalResourceId': event['LogicalResourceId'],
        'NoEcho': no_echo,
        'Data': response_data
    }

    json_response_body = json.dumps(response_body)

    LOGGER.info("Response body:\n" + json_response_body)

    headers = {
        'content-type': '',
        'content-length': str(len(json_response_body))
    }

    try:
        req = urllib.request.Request(response_url,
                                     data=json_response_body.encode('utf-8'),
                                     headers=headers,
                                     method='PUT')
        response = urllib.request.urlopen(req)
        LOGGER.info("Status code: " + response.reason)
    except Exception as e:
        LOGGER.error("send(..) failed executing requests.put(..): " + str(e))