from bottle import post, run, request
import argparse

from requests import get


def parse_args():
    parser = argparse.ArgumentParser(description='Write task logs from Octopus to disk.')
    parser.add_argument('--octopusUrl', dest='octopus_url', action='store', help='The Octopus server URL.',
                        required=True)
    parser.add_argument('--octopusApiKey', dest='octopus_api_key', action='store', help='The Octopus API key',
                        required=True)
    parser.add_argument('--port', dest='port', action='store', help='The port to listen on',
                        required=True, default="8080")

    return parser.parse_args()


def build_headers():
    """
    Build the headers required to access the Octopus API
    :return: A map of headers to send with each Octopus API request
    """
    return {"X-Octopus-ApiKey": args.octopus_api_key}


@post('/')
def webhook():
    """
    Respond to a webhook event generated by an Octopus subscription.
    """
    deployment_id = extract_deployment_id(request.json)
    runbookrun_id = extract_runbookrun_id(request.json)
    space_id = extract_space_id(request.json)

    task_id = None
    if deployment_id is not None:
        task_id = get_deployment_task_id(space_id, deployment_id)
    elif runbookrun_id is not None:
        task_id = get_runbook_task_id(space_id, runbookrun_id)

    write_log(space_id, task_id)


def write_log(space_id, task_id):
    """
    Write the contents of the task log to a file
    :param space_id The space ID
    :param task_id: The task ID whose contents is written to a file
    """
    if task_id is not None:
        task_log = get_task_log(space_id, task_id)
        with open(task_id + ".log", "w") as outfile:
            outfile.write(task_log)


def extract_deployment_id(message):
    """
    Extracts the deployment ID from the Octopus Subscription message.
    :param message: The Subscription message
    :return: The deployment ID
    """
    deployment_ids = [a for a in message["Payload"]["Event"]["RelatedDocumentIds"] if
                      a.startswith("Deployments-")]

    if len(deployment_ids) == 1:
        return deployment_ids[0]

    return None


def extract_runbookrun_id(message):
    """
    Extracts the runbook run ID from the Octopus Subscription message.
    :param message: The Subscription message
    :return: The runbook run ID
    """
    runbookruns_ids = [a for a in message["Payload"]["Event"]["RelatedDocumentIds"] if
                       a.startswith("RunbookRuns-")]

    if len(runbookruns_ids) == 1:
        return runbookruns_ids[0]

    return None


def extract_space_id(message):
    """
    Extract the space ID from the Octopus Subscription message.
    :param message: The Subscription message
    :return: The space ID
    """
    return message["Payload"]["Event"]["SpaceId"]


def get_deployment_task_id(space_id, deployment_id):
    """
    Get the task ID associated with the deployment.
    :param space_id: The space ID
    :param deployment_id: The deployment ID
    :return: The task ID associated with the deployment ID
    """
    deployment_url = args.octopus_url + "/api/" + space_id + "/deployments/" + deployment_id
    response = get(deployment_url, headers=headers)
    deployment_json = response.json()
    return deployment_json["TaskId"]


def get_runbook_task_id(space_id, runbookrun_id):
    """
    Get the task ID associated with the runbook run.
    :param space_id: The space ID
    :param runbookrun_id: The runbook run ID
    :return: The task ID associated with the runbook run ID
    """
    deployment_url = args.octopus_url + "/api/" + space_id + "/runbookruns/" + runbookrun_id
    response = get(deployment_url, headers=headers)
    deployment_json = response.json()
    return deployment_json["TaskId"]


def get_task_log(space_id, task_id):
    """
    Get the task logs. This implementation gets the raw task logs.
    :param space_id: The space ID
    :param task_id: the task ID
    :return: the task logs
    """
    return get(args.octopus_url + "/api/" + space_id + "/tasks/" + task_id + "/raw",
               headers=headers).text


args = parse_args()
headers = build_headers()
run(host='localhost', port=int(args.port), debug=True)
